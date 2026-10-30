#!/usr/bin/env python3
"""Display a safe read-only Organizer task resume view.

Example (paths and pinned hash are supplied by the local owner, not this repo):
  python tools/show_native_task_resume.py \
    --tool /trusted/path/Inventhor.WorkOrganizer.Tool.exe \
    --organizer-root /trusted/local/organizer \
    --tool-sha256 <current approved SHA256> \
    --task <canonical TASK_ID>

This command cannot claim/write, start/stop a service, install or validate QA.
A native host must separately authorize any mutation.
"""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from continuity.organizer_cli_reader import OrganizerCliReader, NativeHandoffUnavailable
from continuity.provider_resume_view import project_native_handoff, ResumeViewInvalid


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Read and project one exact canonical native task (read-only)"
    )
    parser.add_argument("--tool", type=Path, required=True)
    parser.add_argument("--organizer-root", type=Path, required=True)
    parser.add_argument("--tool-sha256", required=True)
    parser.add_argument("--task", required=True)
    args = parser.parse_args(argv)
    try:
        reader = OrganizerCliReader(
            tool_path=args.tool,
            organizer_root=args.organizer_root,
            expected_tool_sha256=args.tool_sha256,
        )
        record = reader.read_task(args.task)
        print(project_native_handoff(record).as_json())
        return 0
    except (NativeHandoffUnavailable, ResumeViewInvalid) as e:
        # Do not echo subprocess output, file contents or secrets.
        code = getattr(e, "code", str(e))
        print("READ_ONLY_HANDOFF_DENIED:" + code, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
