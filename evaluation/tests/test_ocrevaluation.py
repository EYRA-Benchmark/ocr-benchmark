import os
import tempfile
import pytest
import fire
import untangle


@pytest.fixture
def gtXML():
    directory = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.normpath(os.path.join(directory, '../boeken/00538878.xml'))
    return untangle.parse(filename)


@pytest.fixture
def mockXML():
    directory = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.normpath(os.path.join(directory, '../boeken/mock-results/fudged_00538878.xml'))
    return untangle.parse(filename)


def test_ocrevaluation(gtXML, mockXML):
    gtRegion = gtXML.PcGts.Page.TextRegion[0]
    mockRegion = mockXML.PcGts.Page.TextRegion[0]

    gt = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
    mock = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)

    gtName = gt.name
    mockName = mock.name

    gt.write(gtRegion.TextEquiv.Unicode.cdata.encode('utf-8'))
    mock.write(mockRegion.TextEquiv.Unicode.cdata.encode('utf-8'))

    gt.close()
    mock.close()

    #os.unlink(gtName)
    #os.unlink(mockName)
