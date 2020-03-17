#!/usr/bin/env python

import sys
import fire
import untangle
import numpy as np
import tempfile
import cwltool.factory
import pandas as pd
import io
import pathlib
from copy import deepcopy
from shapely.geometry import Polygon, MultiPolygon, box

JACCARD_SCORE_THRESHOLD = 0.9
PIXEL_MATCH_THRESHOLD = 10


def processfile(ground_truth_file, input_file):
    # writeableOutputFile = open(outputfile,"w+")
    gtXML = untangle.parse(ground_truth_file)  #open(ground_truth_file,"r")
    inXML = untangle.parse(input_file)  #open(input_file,"r")

    # processReadingorder(gtXML, inXML)
    processBoundingboxes(gtXML, inXML)
    # processLayout(gtXML, inXML)

    # contents_groundtruth = readableGroundtruthFile.readlines()
    # contents_input = readableInputFile.readlines()

    # readableGroundtruthFile.close()
    # readableInputFile.close()


def processReadingorder(gtXML, inXML):
    print('ReadingOrder')

    # Sort Reading order and print
    gtOrderedGroup = sorted(gtXML.PcGts.Page.ReadingOrder.OrderedGroup.RegionRefIndexed,
                            key=lambda RegionRefIndexed: RegionRefIndexed['index'])
    inOrderedGroup = sorted(inXML.PcGts.Page.ReadingOrder.OrderedGroup.RegionRefIndexed,
                            key=lambda RegionRefIndexed: RegionRefIndexed['index'])
    # accuracy = jaccard_score(gtOrderedGroup, inOrderedGroup, labels=gtOrderedGroup['id'])

    gtReadingOrder = []
    inReadingOrder = []
    for i in range(len(gtOrderedGroup)):
        gtReadingOrder.append(gtOrderedGroup[i]['regionRef'])
    for i in range(len(inOrderedGroup)):
        inReadingOrder.append(inOrderedGroup[i]['regionRef'])

    # gtDict = { i : gtOrderedGroup[i] for i in range(0, len(gtOrderedGroup) ) }
    # inDict = { i : inOrderedGroup[i] for i in range(0, len(inOrderedGroup) ) }

    differences = sum(a != b for a, b in zip(gtReadingOrder, inReadingOrder))
    differences += abs(len(gtReadingOrder) - len(inReadingOrder))
    print('Regions differences: {differences}'.format(differences=differences))

    # for i in range(len(gtOrderedGroup)):
    #     print('{id} : {gtRef} : {inRef}'.format(
    #         id=gtOrderedGroup[i]['index'],
    #         gtRef=gtOrderedGroup[i]['regionRef'],
    #         inRef=inOrderedGroup[i]['regionRef']))


def callCWL(gt_filename, input_filename):
    fac = cwltool.factory.Factory()
    ocrevaluation_performance = fac.make("ocrbenchmark/evaluation/cwl/ocrevaluation-performance.cwl")
    input = {
        'gt': {
            "class": "File",
            "location": pathlib.Path(gt_filename).as_uri()
        },
        'ocr': {
            "class": "File",
            "location": pathlib.Path(input_filename).as_uri()
        }
    }
    return ocrevaluation_performance(**input)


def processTextregions(gtXML, inXML, gt_matches):
    frames = []
    for gt_id, in_id in gt_matches.items():
        # Get the matching textregions

        # TODO: This is probably  wrong!
        gtRegion = gtXML.PcGts.Page.TextRegion[gt_id]
        inRegion = inXML.PcGts.Page.TextRegion[in_id]

        # Write the textregion to temp file
        gt = tempfile.NamedTemporaryFile(suffix='.txt')
        inp = tempfile.NamedTemporaryFile(suffix='.txt')

        gt.write(gtRegion.TextEquiv.Unicode.cdata.encode('utf-8'))
        inp.write(inRegion.TextEquiv.Unicode.cdata.encode('utf-8'))

        gt.flush()
        inp.flush()

        result = callCWL(gt.name, inp.name)
        data = result['global_data']['contents']
        reader = io.StringIO(data)
        frames.append(pd.read_csv(reader, sep=';', index_col='doc_id'))

        gt.close()
        inp.close()

    return pd.concat(frames)


def processBoundingboxes(gtXML, inXML):
    boundingboxes_report = {}
    end_report = 'Boundingbox report\n'

    gtPolygons = getPolygons(gtXML.PcGts.Page)
    inPolygons = getPolygons(inXML.PcGts.Page)

    gtBounds = {}
    inBounds = {}

    for tr_id, polygon in gtPolygons:
        gtBounds[tr_id] = box(*polygon.bounds)
    for tr_id, polygon in inPolygons:
        inBounds[tr_id] = box(*polygon.bounds)

    gtBounds_copy, inBounds_copy, matches, score_single = matchPolygonsAndRemove(gtBounds, inBounds)

    boundingboxes_report.matches = matches

    # print('score_single: ', score_single)

    # end_report = end_report + report

    # All things that are left in the input might (in combination) match with items in the ground truth, so we create unions where the
    # boundaries are within a threshold value on one border (x or y, not both)
    for in_id_a, in_box_a in inBounds.items():
        for in_id_b, in_box_b in inBounds.items():
            if in_id_a != in_id_b:
                (minx_a, miny_a, maxx_a, maxy_a) = in_box_a.bounds
                (minx_b, miny_b, maxx_b, maxy_b) = in_box_b.bounds

                if abs(maxx_b - minx_a) < PIXEL_MATCH_THRESHOLD and abs(
                        miny_b - miny_a) < PIXEL_MATCH_THRESHOLD and abs(maxy_b - maxy_a) < PIXEL_MATCH_THRESHOLD:
                    inBounds_copy['union: ' + in_id_a + ',' + in_id_b] = in_box_a.union(in_box_b)
                    del inBounds_copy[in_id_a]
                    del inBounds_copy[in_id_b]
                    print('created combined boundingbox {newid}'.format(newid=in_id_a + in_id_b))

                elif abs(maxy_b - miny_a) < PIXEL_MATCH_THRESHOLD and abs(
                        minx_b - minx_a) < PIXEL_MATCH_THRESHOLD and abs(maxx_b - maxx_a) < PIXEL_MATCH_THRESHOLD:
                    inBounds_copy['union: ' + in_id_a + ',' + in_id_b] = in_box_a.union(in_box_b)
                    del inBounds_copy[in_id_a]
                    del inBounds_copy[in_id_b]
                    print('created combined boundingbox {newid}'.format(newid=in_id_a + in_id_b))

    gtBounds_rest, inBounds_rest, report, score_merged = matchPolygonsAndRemove(gtBounds_copy, inBounds_copy)
    end_report = end_report + report

    for (gt_id, gt_box) in gtBounds_rest.items():
        end_report = end_report + 'Ground Truth "{gt_id}" did not match anything\n'.format(gt_id=gt_id)

    for in_id, in_box in inBounds_rest.items():
        end_report = end_report + 'Input "{in_id}" did not match anything\n'.format(in_id=in_id)

    end_score = (score_single + score_merged) / len(gtPolygons)

    end_report = end_report + '\nFinal overall bounding box score: {end_score}'.format(end_score=end_score)
    print(end_report)


def matchPolygonsAndRemove(gtBounds, inBounds):
    matches = {}

    gtBounds_copy = deepcopy(gtBounds)
    inBounds_copy = deepcopy(inBounds)
    score = 0
    for gt_id, gt_box in gtBounds.items():
        scores = []
        for _, in_box in inBounds.items():
            score = jaccard_index_multipolygons(gt_box, in_box)
            scores.append(score)

        max_index = np.argmax(scores)

        if scores[max_index] > JACCARD_SCORE_THRESHOLD:
            match_id = list(inBounds.keys())[max_index]

            del inBounds_copy[match_id]
            del gtBounds_copy[gt_id]

            matches[gt_id] = {'id': match_id, 'score': scores[max_index]}

            score = score + scores[max_index]
    return (gtBounds_copy, inBounds_copy, matches, score)


def processLayout(gtXML, inXML):
    print('Layout')

    gtPolygons = getPolygons(gtXML.PcGts.Page)
    inPolygons = getPolygons(inXML.PcGts.Page)

    gtLayout = {}
    inBounds = {}

    for tr_id, polygon in gtPolygons:
        gtLayout[tr_id] = polygon
    for tr_id, polygon in inPolygons:
        inBounds[tr_id] = polygon

    gtLayout_copy = deepcopy(gtLayout)

    for gt_id, gt_box in gtLayout.items():
        scores = []
        for _, in_box in inBounds.items():
            score = jaccard_index_multipolygons(gt_box, in_box)
            scores.append(score)

        max_index = np.argmax(scores)

        if scores[max_index] > JACCARD_SCORE_THRESHOLD:
            match_id = list(inBounds.keys())[max_index]

            del inBounds[match_id]
            del gtLayout_copy[match_id]
            print('"{gt_id}" matched with "{in_id}" with score {score}'.format(in_id=match_id,
                                                                               gt_id=gt_id,
                                                                               score=scores[max_index]))

    for in_id, in_box in inBounds.items():
        print('Input "{in_id}" did not match anything'.format(in_id=in_id))

    for (gt_id, gt_box) in gtLayout_copy.items():
        print('Ground Truth "{gt_id}" did not match anything'.format(gt_id=gt_id))


# def processLayout(gtXML, inXML):
#     print('Textregions layout')

#     gtPolygons = getPolygons(gtXML.PcGts.Page)
#     inPolygons = getPolygons(inXML.PcGts.Page)

#     multi_gt_polygons = MultiPolygon(gtPolygons)
#     multi_in_polygons = MultiPolygon(inPolygons)

#     try:
#         jaccard_score = jaccard_index_multipolygons(multi_gt_polygons, multi_in_polygons)
#         print('Layout jaccard_score: {jaccard_score}'.format(jaccard_score=jaccard_score))
#     except:
#         print('doe moeluk')


def getPolygons(Page):
    polygons = []
    for TextRegion in Page.TextRegion:
        pointslist = []
        for Point in TextRegion.Coords.Point:
            x = int(Point['x'])
            y = int(Point['y'])
            pointslist.append((x, y))

        polygon = Polygon(pointslist)
        polygons.append((TextRegion['id'], polygon))

    return polygons

    # for TextRegion in gtXML.PcGts.Page.TextRegion:
    #     print(TextRegion['id'])
    #     for Point in TextRegion.Coords.Point:
    #         print(Point['x'] + ' ' + Point['y'])

    # for TextRegion in gtXML.PcGts.Page.TextRegion:
    #     print(TextRegion['id'])
    #     for Point in TextRegion.Coords.Point:
    #         print(Point['x'] + ' ' + Point['y'])


def main():
    fire.Fire(processfile)


def jaccard_index_multipolygons(truth_multi, predicted_multi):
    if not (truth_multi.is_valid):
        raise ('The truth multipolygon is not valid!')
    if not (predicted_multi.is_valid):
        raise ('The predicted multipolygon is not valid!')

    # intersection
    intersec = truth_multi.intersection(predicted_multi).area
    # union
    union = truth_multi.union(predicted_multi).area

    # Jaccard index is intersection over union
    return intersec / union


if __name__ == '__main__':
    main()
