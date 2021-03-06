#!/usr/bin/env python
import click
import numpy as np
import json
from glob import glob
from os.path import basename
from ocrbenchmark.evaluation.evaluate_single import process_single


@click.command()
@click.argument('gt_folder',
                type=click.Path(file_okay=False,
                                dir_okay=True,
                                exists=True,
                                readable=True))
@click.argument('in_folder',
                type=click.Path(file_okay=False,
                                dir_okay=True,
                                exists=True,
                                readable=True))
def processall(gt_folder, in_folder):
    filenames = [basename(f) for f in glob(gt_folder + '/*.xml')]
    reports = [
        process_single(gt_folder + '/' + f, in_folder + '/' + f)
        for f in filenames
    ]
    # Aggregate boundingbox scores
    bbox_scores = [r['boundingboxes']['mean'] for r in reports]
    bbox_scores = bbox_scores + [
        r['boundingboxes']['mean_merged'] for r in reports
    ]

    # Aggregate textregion scores
    textregion_scores = {}
    textregion_scores['CER'] = [
        r['textregions']['mean']['CER'] for r in reports
    ]
    textregion_scores['WER'] = [
        r['textregions']['mean']['WER'] for r in reports
    ]
    textregion_scores['WER (order independent)'] = [
        r['textregions']['mean']['WER (order independent)']
        for r in reports
    ]

    output_dict = {
        "metrics": {
            "boundingbox_score":
            np.nanmean(bbox_scores),
            "CER":
            np.nanmean(textregion_scores['CER']),
            "WER":
            np.nanmean(textregion_scores['WER']),
            "WER (order independent)":
            np.nanmean(textregion_scores['WER (order independent)'])
        },
    }
    print(json.dumps(output_dict))


if __name__ == '__main__':
    processall()
