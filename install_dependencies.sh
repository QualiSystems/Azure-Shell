#!/usr/bin/env bash
if [ "${TRAVIS_BRANCH}" = "master" ]
then
    pip install "cloudshell-core>=2.2.0,<2.3.0"
    pip install "cloudshell-shell-core>=3.1.0,<3.2.0"
    pip install "cloudshell-automation-api>=8.0.0.0,<8.1.0.0"
else
    pip install "cloudshell-core>=2.2.0,<2.3.0" --extra-index-url https://testpypi.python.org/simple
    pip install "cloudshell-shell-core>=3.1.0,<3.2.0" --extra-index-url https://testpypi.python.org/simple
    pip install "cloudshell-automation-api>=8.0.0.0,<8.1.0.0" --extra-index-url https://testpypi.python.org/simple
fi

pip install -r test_requirements.txt
pip install coveralls