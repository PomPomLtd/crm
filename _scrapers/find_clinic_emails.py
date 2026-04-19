#!/usr/bin/env python3
"""Entry point — invokes clinic_emails.cli.main().

Usage examples:
    python find_clinic_emails.py --refresh-input          # dump entries from DB
    python find_clinic_emails.py --test https://clinic.ch # diagnose one URL
    python find_clinic_emails.py --sample 20              # try 20 random entries
    python find_clinic_emails.py --workers 10             # full run
    python find_clinic_emails.py --report                 # rebuild CSV + summary
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from clinic_emails.cli import main

if __name__ == "__main__":
    main()
