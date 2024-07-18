# Copyright 2021 Arbaaz Laskar

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typer.testing import CliRunner
from fichub_cli_metadata.cli import app
from fichub_cli_metadata import __version__


def test_cli_url_input(tmpdir):
    print("----------------------------------------")
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(app, [
            '-ai', 'https://www.fanfiction.net/s/11783284/1/Doppelgängland', '-d'])

    assert not result.exception
    assert result.exit_code == 0


def test_cli_version():
    print("----------------------------------------")
    runner = CliRunner()
    result = runner.invoke(app, ['--version'])
    
    assert not result.exception
    assert result.exit_code == 0
    assert result.output.strip() == 'fichub-cli-metadata: v0.6.5'
