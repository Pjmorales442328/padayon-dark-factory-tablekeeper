"""Owned stage-4 adapter for the inherited stage-3 history-validation import check (ledger 281, 272).

The frozen test_s3_transfer.ImportValidation3.test_L281_L272_* picks the longest list of dicts that carry "seq". Stage 4 adds a
restaurant event list ("restaurant_events", ledger 340ff) whose entries also carry "seq" but not the reservation fields, so the frozen
test indexes a key that list never had. The frozen test stays visible (SUPERSEDED in run_stage4.py); this adapter runs the same
mutations against RESERVATION histories only, selected by shape: every entry has seq, event, changes and revision.
"""
import copy

import s4common  # noqa: F401  (points the frozen helpers at stage-4 before they are imported)
from test_s3_transfer import ImportValidation3
from test_e_transfer import walk, get_at


class ImportValidation4(ImportValidation3):
    def test_L281_L272_history_sequence_and_events_are_validated(self):
        st0 = self.exp["state"]
        need = {"seq", "event", "changes", "revision"}
        lists = [(p, n) for p, n in walk(st0)
                 if isinstance(n, list) and len(n) >= 2 and all(isinstance(e, dict) and need <= set(e) for e in n)]
        self.assertTrue(lists, "reservation histories (seq/event/changes/revision) must be present in the exported state")
        p, n = max(lists, key=lambda x: len(x[1]))
        variants = []
        v = copy.deepcopy(n); v[0], v[1] = v[1], v[0]; variants.append(v)                      # out of seq order
        v = copy.deepcopy(n); v[1]["seq"] = v[0]["seq"]; variants.append(v)                    # duplicate seq
        v = copy.deepcopy(n); v[1]["seq"] = 7; variants.append(v)                              # gap
        v = copy.deepcopy(n); v[1]["event"] = "exploded"; variants.append(v)
        v = copy.deepcopy(n); v[0]["event"] = "changed"; variants.append(v)                    # history must start with creation
        v = copy.deepcopy(n); del v[0]; variants.append(v)
        v = copy.deepcopy(n); v[1]["revision"] = v[0]["revision"] + 5; variants.append(v)
        v = copy.deepcopy(n); v[1]["changes"] = "x"; variants.append(v)
        for rep in variants:
            st = copy.deepcopy(st0)
            get_at(st, p[:-1])[p[-1]] = rep
            r = self.imp(st)
            self.assertLess(r.status, 500)
            self.err(r, 422, "validation_failed")
            self.unchanged(str(rep)[:80])
