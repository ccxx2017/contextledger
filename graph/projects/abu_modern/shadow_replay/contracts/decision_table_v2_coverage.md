# Decision Table v2 Coverage Report

| Rule ID | Domain | Covers Cases |
| --- | --- | --- |
| R001 | adjudication_key | lc_multi_claim_partial, tr_syn_partial_policy_clause |
| R002 | adjudication_key | tr_alias_workspace_identity, tr_alias_quant_tools |
| R003 | adjudication_key | tr_syn_partial_policy_clause, tr_syn_partial_checklist_clause |
| R004 | adjudication_key | tr_full_tkt_005b, tr_full_tkt_006, tr_revival_round5x |
| R005 | adjudication_key | lc_multi_claim_partial, tr_syn_partial_policy_clause |
| R006 | adjudication_key | tr_syn_conditional_region_exception, tr_syn_non_invalidation_parallel_targets |
| R007 | relation | lc_two_lifecycles_no_kill, lc_legacy_migration |
| R008 | relation | lc_diff_source_conflict, tr_syn_revival_feature_flag, tr_syn_provenance_conflict, tr_prov_run54b |
| R009 | time_ordering | lc_late_arrival, tr_syn_out_of_order_inventory_present |
| R010 | time_ordering | tr_syn_out_of_order_inventory_present |
| R011 | time_ordering | lc_late_arrival |
| R012 | terminal_state | lc_revival |
| R013 | revival | lc_revival |
| R014 | alias | lc_alias_abstain |
