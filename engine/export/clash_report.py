import csv
from pathlib import Path

from .base import Exporter


class ClashReportContext:
    """Canonical report context for clash review exports."""

    def __init__(self, workspace, results=None, group_by="Severity", title="Clash Report", template=None):

        self.workspace = workspace
        self.manager = workspace.clash_manager
        self.results = list(results if results is not None else self.manager.results)
        self.group_by = group_by
        self.title = title
        self.template = template or {}

    def target_path(self, path):
        """Normalize an export destination path."""

        return Path(path)


class ClashReportGenerator:
    """Generates PDF and CSV clash reports through exporter-style adapters."""

    def __init__(self):

        self._exporters = {
            "csv": ClashCSVReportExporter(),
            "pdf": ClashPDFReportExporter(),
        }

    def export(self, workspace, path, format_name=None, results=None, group_by=None, template_name=None):
        """Export a clash report and return the destination path."""

        key = str(format_name or Path(path).suffix.lstrip(".") or "pdf").lower()
        exporter = self._exporters.get(key)

        if exporter is None:
            raise ValueError(f"Unsupported clash report format: {key}")

        manager = workspace.clash_manager
        template = manager.report_template(template_name or manager.report_settings.get("template", "Detailed Report"))
        chosen_group = group_by or template.get("group_by") or manager.report_settings.get("group_by", "Severity")
        context = ClashReportContext(
            workspace,
            results,
            chosen_group,
            template.get("name", "Clash Report"),
            template,
        )

        return exporter.export(context, path)


class ClashCSVReportExporter(Exporter):
    """Exports clash review data to CSV."""

    extension = "csv"
    format_name = "Clash CSV"

    def export(self, context, path):
        """Write a CSV clash report."""

        target = context.target_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)

        with target.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow([
                "Name",
                "Type",
                "Severity",
                "Priority",
                "Status",
                "Reviewer",
                "Owner",
                "Due Date",
                "Resolution Category",
                "Approval State",
                "Watch List",
                "Review Queue",
                "Discipline",
                "Entity A",
                "Entity B",
                "Category",
                "Comments",
                "Resolution Notes",
            ])

            for result in context.results:
                writer.writerow([
                    result.name,
                    result.clash_type,
                    result.severity,
                    result.priority,
                    result.status,
                    result.assigned_reviewer,
                    result.owner,
                    result.due_date,
                    result.resolution_category,
                    result.approval_state,
                    result.watch_list,
                    result.review_queue,
                    result.discipline,
                    result.entity_a_name,
                    result.entity_b_name,
                    result.category,
                    result.comments,
                    result.resolution_notes,
                ])

        return target

    def serialize(self, context):
        """Return an in-memory CSV representation."""

        lines = [
            "Name,Type,Severity,Priority,Status,Reviewer,Owner,Due Date,Resolution Category,Approval State,Watch List,Review Queue,Discipline,Entity A,Entity B,Category,Comments,Resolution Notes"
        ]
        for result in context.results:
            lines.append(",".join(str(value) for value in [
                result.name,
                result.clash_type,
                result.severity,
                result.priority,
                result.status,
                result.assigned_reviewer,
                result.owner,
                result.due_date,
                result.resolution_category,
                result.approval_state,
                str(result.watch_list),
                str(result.review_queue),
                result.discipline,
                result.entity_a_name,
                result.entity_b_name,
                result.category,
                result.comments,
                result.resolution_notes,
            ]))

        return "\n".join(lines)


class ClashPDFReportExporter(Exporter):
    """Exports clash review data to a lightweight vector PDF."""

    extension = "pdf"
    format_name = "Clash PDF"

    def export(self, context, path):
        """Write a PDF clash report."""

        target = context.target_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(self.serialize_bytes(context))

        return target

    def serialize(self, context):
        """Return a Latin-1 PDF string."""

        return self.serialize_bytes(context).decode("latin-1")

    def serialize_bytes(self, context):
        """Return report PDF bytes."""

        lines = self._report_lines(context)
        content = self._content_stream(lines)
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
            f"<< /Length {len(content)} >>\nstream\n".encode("latin-1") + content + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ]

        return self._pdf(objects)

    def _report_lines(self, context):

        stats = context.manager.statistics
        lines = [
            context.title,
            f"Total: {stats.total}  Open: {stats.unresolved}",
            f"Grouped by: {context.group_by}",
            f"Template: {context.template.get('name', context.title)}",
            "",
        ]
        grouped = context.manager.grouped_results(context.results, context.group_by)

        for group, results in grouped.items():
            lines.append(f"{group} ({len(results)})")
            for result in results:
                lines.append(
                    f"- {result.name}: {result.status} / {result.severity} / "
                    f"{result.entity_a_name} vs {result.entity_b_name}"
                )
                lines.append(
                    f"  Owner: {result.owner or 'Unassigned'}  Due: {result.due_date or 'None'}  "
                    f"Approval: {result.approval_state}"
                )
                if result.assigned_reviewer:
                    lines.append(f"  Reviewer: {result.assigned_reviewer}")
                if result.comments and context.template.get("include_comments", True):
                    lines.append(f"  Comments: {result.comments}")

        return lines

    def _content_stream(self, lines):

        commands = ["BT", "/F1 11 Tf", "40 752 Td"]

        for index, line in enumerate(lines[:48]):
            if index:
                commands.append("0 -14 Td")
            commands.append(f"({self._escape(line)}) Tj")

        commands.append("ET")

        return "\n".join(commands).encode("latin-1", errors="replace")

    def _pdf(self, objects):

        chunks = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
        offsets = [0]

        for index, obj in enumerate(objects, start=1):
            offsets.append(sum(len(chunk) for chunk in chunks))
            chunks.append(f"{index} 0 obj\n".encode("latin-1"))
            chunks.append(obj if isinstance(obj, bytes) else obj.encode("latin-1"))
            chunks.append(b"\nendobj\n")

        xref = sum(len(chunk) for chunk in chunks)
        chunks.append(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
        chunks.append(b"0000000000 65535 f \n")

        for offset in offsets[1:]:
            chunks.append(f"{offset:010d} 00000 n \n".encode("latin-1"))

        chunks.append(
            f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref}\n%%EOF\n".encode("latin-1")
        )

        return b"".join(chunks)

    def _escape(self, text):

        return str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
