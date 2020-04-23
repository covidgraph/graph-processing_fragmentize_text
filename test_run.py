from run import create_query_link_fragments


def test_query_link_fragments():

    q = create_query_link_fragments('Test')

    assert q