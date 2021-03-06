#!/usr/bin/env python

import difflib
import io
import json
import logging
import pathlib
import sys
import tempfile
from copy import deepcopy

import click
import cwltool.factory
import cwltool.loghandler
import numpy as np
import pandas as pd
import untangle
from shapely.geometry import MultiPolygon, Polygon, box

JACCARD_SCORE_THRESHOLD = 0.9
PIXEL_MATCH_THRESHOLD = 10

# Do not log so much with cwltool
cwltool.loghandler._logger.setLevel(logging.WARN)


def process_single(gt_file, in_file):
    print("processing ${gt_file} and ${in_file}".format(gt_file=gt_file, in_file=in_file))
    overall_report = {}
    # writeableOutputFile = open(outputfile,"w+")
    gtXML = untangle.parse(gt_file)  # open(ground_truth_file,"r")
    inXML = untangle.parse(in_file)  # open(input_file,"r")

    if (hasattr(gtXML, "PcGts") and hasattr(inXML, "PcGts")
            and hasattr(gtXML.PcGts, "Page") and hasattr(inXML.PcGts, "Page")):

        matches_for_text_processing, boundingboxes_report = processBoundingboxes(
            gtXML, inXML)
        overall_report['boundingboxes'] = boundingboxes_report

        readingorder_report = processReadingorder(gtXML, inXML,
                                                  matches_for_text_processing)
        overall_report['readingorder'] = readingorder_report

        textregion_report = processTextregions(gtXML, inXML,
                                               matches_for_text_processing)
        overall_report['textregions'] = textregion_report
    else:
        overall_report = {
            'boundingboxes': {
                'mean': np.nan,
                'mean_merged': np.nan,
                'nr_false_positives': np.nan,
                'nr_false_negatives': np.nan
            },
            'readingorder': "",
            'textregions': {
                'CER': np.nan,
                'WER': np.nan,
                'WER (order independent)': np.nan
            },
        }

    print(overall_report)

    return overall_report


@click.command()
@click.argument('gt_file', type=click.File(encoding='utf-8'))
@click.argument('in_file', type=click.File(encoding='utf-8'))
def processfile(gt_file, in_file):
    report = process_single(gt_file, in_file)
    print(json.dumps(report, indent=4, sort_keys=True))


def processReadingorder(gtXML, inXML, matches_for_text_processing):
    report = {}

    if (hasattr(gtXML.PcGts.Page, 'ReadingOrder')
            and hasattr(inXML.PcGts.Page, 'ReadingOrder')
            and hasattr(gtXML.PcGts.Page.ReadingOrder, 'OrderedGroup')
            and hasattr(inXML.PcGts.Page.ReadingOrder, 'OrderedGroup')):
        # Sort Reading orders by index
        gtOrderedGroup = sorted(
            gtXML.PcGts.Page.ReadingOrder.OrderedGroup.RegionRefIndexed,
            key=lambda RegionRefIndexed: RegionRefIndexed['index'])
        inOrderedGroup = sorted(
            inXML.PcGts.Page.ReadingOrder.OrderedGroup.RegionRefIndexed,
            key=lambda RegionRefIndexed: RegionRefIndexed['index'])

        # Read the reading order of the Ground truth file.
        gtReadingOrder = []
        for i in range(len(gtOrderedGroup)):
            gtReadingOrder.append(gtOrderedGroup[i]['regionRef'])

        # Translate to the names given in the input file with help of the matched bounding boxes.
        inTranslatedReadingOrder = []
        for match in gtReadingOrder:
            if (match in matches_for_text_processing):
                inTranslatedReadingOrder.append(
                    matches_for_text_processing[match])

        # Read the reading order of the input file.
        inReadingOrder = []
        for i in range(len(inOrderedGroup)):
            inReadingOrder.append(inOrderedGroup[i]['regionRef'])

        # Compare using difflib
        a = inTranslatedReadingOrder
        b = inReadingOrder

        s = difflib.SequenceMatcher(None, a, b)
        for tag, i1, i2, j1, j2 in s.get_opcodes():
            report = ("%7s a[%d:%d] (%s) b[%d:%d] (%s)" %
                      (tag, i1, i2, a[i1:i2], j1, j2, b[j1:j2]))
    else:
        report = ""

    return report


def callCWL(gt_filename, input_filename):
    fac = cwltool.factory.Factory()
    ocrevaluation_performance = fac.make(
        "ocrbenchmark/evaluation/ocrevaluation/ocrevaluation-performance.cwl")
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


def processTextregions(gtXML, inXML, matches_for_text_processing):
    frames = []
    report = {}

    gtRegions = getTextregions(gtXML.PcGts.Page)
    inRegions = getTextregions(inXML.PcGts.Page)

    # For all Ground truth text regions
    for gt_region in gtRegions:
        gt_region_id = gt_region[0]
        gt_region_text = gt_region[1].TextEquiv.Unicode.cdata

        # Translate the id to the input file's TextRegion id using the boundingbox data
        if (gt_region_id in matches_for_text_processing):
            inTranslatedRegionName = matches_for_text_processing[gt_region_id]

            # Extract the matching input file Textregion
            # Write tmp files
            gt_file = tempfile.NamedTemporaryFile(suffix='.txt')
            gt_file.write(gt_region_text.encode('utf-8'))

            # Writes normal and combined regions to file
            in_file = tempfile.NamedTemporaryFile(suffix='.txt')
            for in_region in inRegions:
                if (in_region[0] in inTranslatedRegionName):
                    in_region_text = in_region[1].TextEquiv.Unicode.cdata

                    in_file.write(in_region_text.encode('utf-8'))

            gt_file.flush()
            in_file.flush()

            # call OCREvaluation through CWL workflow and write input to frames
            result = callCWL(gt_file.name, in_file.name)
            data = result['global_data']['contents']
            reader = io.StringIO(data)

            # Extract result from csv file
            df = pd.read_csv(reader, sep=';')
            df['region_id'] = inTranslatedRegionName

            # Manipulate the result into a nice frame
            df = df.set_index('region_id')
            df = df.drop('doc_id', axis=1)

            frames.append(df)

            gt_file.close()
            in_file.close()

    if len(frames) > 0:
        df = pd.concat(frames)
        mean = df.mean(axis=0)
        report = df.transpose().to_dict()
        report['mean'] = mean.to_dict()
    else:
        report = {
            'mean': {
                'CER': np.nan,
                'WER': np.nan,
                'WER (order independent)': np.nan
            }
        }

    return report


def processBoundingboxes(gtXML, inXML):
    report = {}
    matches_for_text_processing = {}

    gtPolygons = getPolygons(gtXML.PcGts.Page)
    inPolygons = getPolygons(inXML.PcGts.Page)

    gtBounds = {}
    inBounds = {}

    for tr_id, polygon in gtPolygons:
        gtBounds[tr_id] = box(*polygon.bounds)
    for tr_id, polygon in inPolygons:
        inBounds[tr_id] = box(*polygon.bounds)

    # Search for and get all of the direct matches. gtBounds_copy and inBounds_copy will house the remaining entries only.
    gtBounds_copy, inBounds_copy, matches_singles, score_singles = matchPolygonsAndRemove(
        gtBounds, inBounds)
    report['matches'] = matches_singles
    report['mean'] = score_singles

    # All things that are left in the input might (in combination) match with items in the ground truth, so we create unions where the
    # boundaries are within a threshold value on one border and follow one another in the Y direction (aka are underneath eachother),
    # these are 'merged' matches.
    for in_id_a, in_box_a in gtBounds_copy.items():
        for in_id_b, in_box_b in inBounds_copy.items():
            if in_id_a != in_id_b:
                (minx_a, miny_a, maxx_a, maxy_a) = in_box_a.bounds
                (minx_b, miny_b, maxx_b, maxy_b) = in_box_b.bounds

                # Check the vertical only
                if abs(maxy_b - miny_a) < PIXEL_MATCH_THRESHOLD and \
                        abs(minx_b - minx_a) < PIXEL_MATCH_THRESHOLD and \
                        abs(maxx_b - maxx_a) < PIXEL_MATCH_THRESHOLD:

                    inBounds_copy[in_id_b + ','
                                  + in_id_a] = in_box_a.union(in_box_b)
                    del inBounds_copy[in_id_a]
                    del inBounds_copy[in_id_b]

    # The compounded boxes are now matched with the remaining boxes in the ground truth file.
    # gtBounds_rest and inBounds_rest will house the remaining entries only.
    gtBounds_rest, inBounds_rest, matches_merged, score_merged = matchPolygonsAndRemove(gtBounds_copy, inBounds_copy)
    report['matches_merged'] = matches_merged
    report['mean_merged'] = score_merged

    # Record the remaining entries
    report['false_negatives'] = list(gtBounds_rest.keys())
    report['false_positives'] = list(inBounds_rest.keys())

    for match in report['matches']:
        matches_for_text_processing[match] = report['matches'][match]['id']
    for match in report['matches_merged']:
        matches_for_text_processing[match] = report['matches_merged'][match]['id']

    return matches_for_text_processing, report


def matchPolygonsAndRemove(gtBounds, inBounds):
    matches = {}
    final_scores = []

    gtBounds_copy = deepcopy(gtBounds)
    inBounds_copy = deepcopy(inBounds)

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
            final_scores.append(scores[max_index])

    final_score = np.average(final_scores)
    # if (len(matches) > 0):
    #     final_score = np.sum(scores) / len(matches)

    return (gtBounds_copy, inBounds_copy, matches, final_score)


def processLayout(gtXML, inXML):
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
            print('"{gt_id}" matched with "{in_id}" with score {score}'.format(
                in_id=match_id, gt_id=gt_id, score=scores[max_index]))

    for in_id, in_box in inBounds.items():
        print('Input "{in_id}" did not match anything'.format(in_id=in_id))

    for (gt_id, gt_box) in gtLayout_copy.items():
        print('Ground Truth "{gt_id}" did not match anything'.format(
            gt_id=gt_id))


def getPolygons(Page):
    polygons = []
    if hasattr(Page, 'TextRegion'):
        for TextRegion in Page.TextRegion:
            pointslist = []
            for Point in TextRegion.Coords.Point:
                x = int(Point['x'])
                y = int(Point['y'])
                pointslist.append((x, y))

            polygon = Polygon(pointslist)
            polygons.append((TextRegion['id'], polygon))

    return polygons


def getTextregions(Page):
    textregions = []
    if hasattr(Page, 'TextRegion'):
        for TextRegion in Page.TextRegion:
            textregions.append((TextRegion['id'], TextRegion))

    return textregions


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
    processfile()
