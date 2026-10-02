class NovelGenerationError(Exception):
    """AI не смог сгенерировать описание."""


class ActiveJobAlreadyExistsError(Exception):
    """Активная задача с таким dedup_key уже существует."""


class GenerationJobNotFoundError(Exception):
    def __init__(self, job_id: int):
        self.job_id = job_id
        super().__init__(f"Generation job {job_id} not found")
