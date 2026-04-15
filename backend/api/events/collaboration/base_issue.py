from events.collaboration.base_collaboration import BaseCollaboration


class BaseIssueEvent(BaseCollaboration):
    _notification_subtopic = "issue"

    def pre_processing(self):
        super().pre_processing()
        self._issue_wo_key = None
        issue_data = getattr(self.info, 'issue_data', None)
        if issue_data and isinstance(issue_data, dict) and issue_data.get('_key'):
            cursor = self.tx.aql.execute(
                "FOR rel IN issue_rel "
                "FILTER rel._from == @issue_id AND STARTS_WITH(rel._to, 'WorkOrder/') "
                "RETURN PARSE_IDENTIFIER(rel._to).key",
                bind_vars={"issue_id": f"Issue/{issue_data['_key']}"}
            )
            self._issue_wo_key = next(cursor, None)

    def _build_event_payload(self):
        payload = super()._build_event_payload()
        if not payload:
            return payload
        wo_key = getattr(self, '_issue_wo_key', None)
        if not wo_key:
            issue_data = getattr(self.info, 'issue_data', None)
            if issue_data and isinstance(issue_data, dict):
                for link in issue_data.get('linked_to', []):
                    if link.get('type') == 'work_order':
                        wo_key = link['key']
                        break
        if wo_key:
            payload['work_order_key'] = wo_key
        return payload
