import enum


class JobKind(str, enum.Enum):
    NOVEL = "novel"
    SCENE = "scene"


class JobStatus(str, enum.Enum):
    CREATED = "created"
    PUBLISHING = "publishing"
    SENT = "sent"
    DONE = "done"
    FAILED = "failed"

    @classmethod
    def active(cls) -> tuple["JobStatus", ...]:
        return (cls.CREATED, cls.PUBLISHING, cls.SENT)
