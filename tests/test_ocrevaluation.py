import os
import tempfile
import pytest
import fire
import untangle
import cwltool.factory
import pandas as pd
import io


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

    #gt = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
    #mock = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)

    #gt_name = gt.name
    #mock_name = mock.name

    #gt.write(gtRegion.TextEquiv.Unicode.cdata.encode('utf-8'))
    #mock.write(mockRegion.TextEquiv.Unicode.cdata.encode('utf-8'))

    fac = cwltool.factory.Factory()
    echo = fac.make("ocrbenchmark/evaluation/cwl/ocrevaluation-performance.cwl")
    input = {
        'gt': {
            "class": "File",
            "basename": "gt.txt",
            "contents": gtRegion.TextEquiv.Unicode.cdata
        },
        'ocr': {
            "class": "File",
            "basename": "ocr.txt",
            "contents": mockRegion.TextEquiv.Unicode.cdata
        }
    }
    result = echo(**input)

    data = result['global_data']['contents']
    reader = io.StringIO(data)
    df = pd.read_csv(reader, sep=';', index_col='doc_id')

    assert (df['CER']['gt_out'] == 2.78)

    # gt.close()
    # mock.close()

    #os.unlink(gtName)
    #os.unlink(mockName)
