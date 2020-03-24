#!/usr/bin/env python
import click
import statistics
import json
from glob import glob
from os.path import basename
from ocrbenchmark.evaluation.evaluate_single import process_single

@click.command()
@click.argument('gt_folder', type=click.Path(file_okay=False, dir_okay=True, exists=True, readable=True))
@click.argument('in_folder', type=click.Path(file_okay=False, dir_okay=True, exists=True, readable=True))
def processall(gt_folder, in_folder):
    filenames = [basename(f) for f in glob(gt_folder + '/*.xml')]
    reports = [process_single(gt_folder + '/' + f, in_folder + '/' + f) for f in filenames]
    scores = [r['boundingboxes']['score'] for r in reports]
    output_dict = {
            "metrics": { "score": statistics.mean(scores) }
    }
    print(json.dumps(output_dict))

if __name__ == '__main__':
    processall()
