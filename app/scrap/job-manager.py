
import uuid
import docker

client = docker.from_env()


def crear_job(url):

    job_id = str(uuid.uuid4())

    container = client.containers.run(
        "scrap-worker:latest",

        environment={
            "JOB_ID": job_id,
            "TARGET_URL": url,
        },

        detach=True,

        name=f"scraping-{job_id}",

        ports={
            "6080/tcp": None
        }
    )

    return job_id, container.id