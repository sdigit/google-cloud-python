# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Get the inserted gRPC lines for datastore pb2 file."""

import os
import shutil
import subprocess
import sys
import tempfile

from script_utils import PROJECT_ROOT


PROTOS_DIR = os.path.join(PROJECT_ROOT, 'googleapis-pb')
PROTO_PATH = os.path.join(PROTOS_DIR, 'google', 'datastore',
                          'v1', 'datastore.proto')
GRPC_ONLY_FILE = os.path.join(PROJECT_ROOT, 'datastore',
                              'google', 'cloud', 'datastore',
                              '_generated', 'datastore_grpc_pb2.py')
GRPCIO_VIRTUALENV = os.getenv('GRPCIO_VIRTUALENV')
if GRPCIO_VIRTUALENV is None:
    PYTHON_EXECUTABLE = sys.executable
else:
    PYTHON_EXECUTABLE = os.path.join(GRPCIO_VIRTUALENV, 'bin', 'python')
MESSAGE_SNIPPET = ' = _reflection.GeneratedProtocolMessageType('
IMPORT_TEMPLATE = (
    'from google.cloud.datastore._generated.datastore_pb2 import %s\n')


def get_pb2_contents_with_grpc():
    """Get pb2 lines generated by protoc with gRPC plugin.

    :rtype: list
    :returns: A list of lines in the generated file.
    """
    temp_dir = tempfile.mkdtemp()
    generated_path = os.path.join(temp_dir, 'google', 'datastore',
                                  'v1', 'datastore_pb2.py')
    try:
        return_code = subprocess.call([
            PYTHON_EXECUTABLE,
            '-m',
            'grpc.tools.protoc',
            '--proto_path',
            PROTOS_DIR,
            '--python_out',
            temp_dir,
            '--grpc_python_out',
            temp_dir,
            PROTO_PATH,
        ])
        if return_code != 0:
            sys.exit(return_code)
        with open(generated_path, 'rb') as file_obj:
            return file_obj.readlines()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def get_pb2_contents_without_grpc():
    """Get pb2 lines generated by protoc without gRPC plugin.

    :rtype: list
    :returns: A list of lines in the generated file.
    """
    temp_dir = tempfile.mkdtemp()
    generated_path = os.path.join(temp_dir, 'google', 'datastore',
                                  'v1', 'datastore_pb2.py')
    try:
        return_code = subprocess.call([
            PYTHON_EXECUTABLE,
            '-m',
            'grpc.tools.protoc',
            '--proto_path',
            PROTOS_DIR,
            '--python_out',
            temp_dir,
            PROTO_PATH,
        ])
        if return_code != 0:
            sys.exit(return_code)
        with open(generated_path, 'rb') as file_obj:
            return file_obj.readlines()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def get_pb2_grpc_only():
    """Get pb2 lines that are only in gRPC.

    :rtype: list
    :returns: A list of lines that are only in the pb2 file
              generated with the gRPC plugin.
    """
    grpc_contents = get_pb2_contents_with_grpc()
    non_grpc_contents = get_pb2_contents_without_grpc()

    grpc_only_lines = []
    curr_non_grpc_line = 0
    for line in grpc_contents:
        if line == non_grpc_contents[curr_non_grpc_line]:
            curr_non_grpc_line += 1
        else:
            grpc_only_lines.append(line)

    return grpc_only_lines


def get_pb2_message_types():
    """Get message types defined in datastore pb2 file.

    :rtype: list
    :returns: A list of names that are defined as message types.
    """
    non_grpc_contents = get_pb2_contents_without_grpc()
    result = []
    for line in non_grpc_contents:
        if MESSAGE_SNIPPET in line:
            name, _ = line.split(MESSAGE_SNIPPET)
            result.append(name)

    return sorted(result)


def main():
    """Write gRPC-only lines to custom module."""
    grpc_only_lines = get_pb2_grpc_only()
    with open(GRPC_ONLY_FILE, 'wb') as file_obj:
        # First add imports for public objects in the original.
        file_obj.write('# BEGIN: Imports from datastore_pb2\n')
        for name in get_pb2_message_types():
            import_line = IMPORT_TEMPLATE % (name,)
            file_obj.write(import_line)
        file_obj.write('#   END: Imports from datastore_pb2\n')
        file_obj.write(''.join(grpc_only_lines))


if __name__ == '__main__':
    main()
