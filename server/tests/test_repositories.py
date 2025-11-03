from raspberrypiserver.repositories import InMemoryScanRepository


def test_inmemory_repository_capacity():
    repo = InMemoryScanRepository(capacity=2)
    repo.save({"order": 1})
    repo.save({"order": 2})
    repo.save({"order": 3})

    assert list(repo.recent()) == [{"order": 2}, {"order": 3}]
    assert list(repo.recent(limit=1)) == [{"order": 3}]
    assert list(repo.recent(limit=0)) == []
