from quickpub import (
    publish,
    Version,
    MypyRunner,
    PylintRunner,
    UnittestRunner,
    PypircEnforcer,
    LocalVersionEnforcer,
    ReadmeEnforcer,
    PypiRemoteVersionEnforcer,
    LicenseEnforcer,
    GithubUploadTarget,
    PypircUploadTarget,
    SetuptoolsBuildSchema,
    CondaPythonProvider,
    DefaultPythonProvider,
)
from tqdm import tqdm


def main() -> None:
    publish(
        name="githooklib",
        version="0.0.1",
        author="danielnachumdev",
        author_email="danielnachumdev@gmail.com",
        description="A Python framework for creating, managing, and installing Git hooks with automatic discovery and CLI tools.",
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
        global_quality_assurance_runners=[
            # MypyRunner(bound="<=150", configuration_path="./mypy.ini"),
            # PylintRunner(bound=">=0.8", configuration_path="./.pylintrc"),
            # UnittestRunner(bound=">=0.8"),
        ],
        pbar=tqdm(desc="QA", leave=False),  # type: ignore
    )


if __name__ == "__main__":
    main()
