from dataclasses import dataclass

from parsers.schema import Document
from parsers.opt_parser import OptRecord


@dataclass
class CrossRefIssue:
    doc_id: str
    issue_type: str   # 'missing_in_opt', 'missing_in_dat', 'path_not_found'
    detail: str


def validate_crossref(documents: list[Document],
                      opt_records: list[OptRecord]) -> list[CrossRefIssue]:
    issues = []
    dat_ids = {doc.begdoc for doc in documents}
    opt_ids = {r.begdoc for r in opt_records if r.first_page}

    for doc_id in sorted(dat_ids - opt_ids):
        issues.append(CrossRefIssue(doc_id, 'missing_in_opt',
            f"{doc_id} in DAT has no corresponding OPT entry"))

    for doc_id in sorted(opt_ids - dat_ids):
        issues.append(CrossRefIssue(doc_id, 'missing_in_dat',
            f"{doc_id} in OPT has no corresponding DAT record"))

    return issues
