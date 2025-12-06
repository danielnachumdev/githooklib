from quickpub import (
    publish,
    Version,
    PypircEnforcer,
    LocalVersionEnforcer,
    ReadmeEnforcer,
    PypiRemoteVersionEnforcer,
    LicenseEnforcer,
    GithubUploadTarget,
    PypircUploadTarget,
    SetuptoolsBuildSchema,
    DefaultPythonProvider,
)
from tqdm import tqdm
from githooklib.__main__ import main as entry_point


def main() -> None:
    publish(
        name="githooklib",
        version="0.0.1",
        author="danielnachumdev",
        author_email="danielnachumdev@gmail.com",
        description="A Python framework (and CLI) for creating, managing, and installing Git hooks with python",
        min_python=Version(3, 8, 0),
        dependencies=["fire"],
        homepage="https://github.com/danielnachumdev/githooklib",
        enforcers=[
            PypircEnforcer(),
            ReadmeEnforcer(),
            LicenseEnforcer(),
            LocalVersionEnforcer(),
            PypiRemoteVersionEnforcer(),
        ],
        build_schemas=[SetuptoolsBuildSchema()],
        upload_targets=[PypircUploadTarget(), GithubUploadTarget()],
        python_interpreter_provider=DefaultPythonProvider(),
        global_quality_assurance_runners=[],
        scripts={"githooklib": entry_point, "githooks": entry_point},
        pbar=tqdm(desc="QA", leave=False),  # type: ignore
        demo=True,
    )


if __name__ == "__main__":
    main()
