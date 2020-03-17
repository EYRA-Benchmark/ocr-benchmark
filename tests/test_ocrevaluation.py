import os
import tempfile
import pytest
import fire
import untangle
import cwltool.factory
import pandas as pd
import io
import pathlib


@pytest.fixture
def gtXML():
    directory = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.normpath(os.path.join(directory, '../ocrbenchmark/evaluation/boeken/00538878.xml'))
    return untangle.parse(filename)


@pytest.fixture
def mockXML():
    directory = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.normpath(
        os.path.join(directory, '../ocrbenchmark/evaluation/boeken/mock-results/fudged_00538878.xml'))
    return untangle.parse(filename)


def test_ocrevaluation(gtXML, mockXML):
    gtRegion = gtXML.PcGts.Page.TextRegion[2]
    mockRegion = mockXML.PcGts.Page.TextRegion[2]

    gt = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
    mock = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)

    gt_name = gt.name
    mock_name = mock.name

    # Write temp files
    gt.write(gtRegion.TextEquiv.Unicode.cdata.encode('utf-8'))
    mock.write(mockRegion.TextEquiv.Unicode.cdata.encode('utf-8'))

    gt.flush()
    mock.flush()

    fac = cwltool.factory.Factory()
    ocrevaluation_performance = fac.make("ocrbenchmark/evaluation/cwl/ocrevaluation-performance.cwl")
    input = {
        'gt': {
            "class": "File",
            "location": pathlib.Path(gt_name).as_uri()
        },
        'ocr': {
            "class": "File",
            "location": pathlib.Path(mock_name).as_uri()
        }
    }
    result = ocrevaluation_performance(**input)

    data = result['global_data']['contents']
    reader = io.StringIO(data)
    df = pd.read_csv(reader, sep=';', index_col='doc_id')

    gt.close()
    mock.close()

    os.unlink(gt_name)
    os.unlink(mock_name)

    assert (df['CER'][0] == 2.78)
