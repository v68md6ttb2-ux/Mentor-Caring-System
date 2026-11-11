"""Report export control logic."""

from app.mapper.record_mapper import RecordExportMapper, WordFileMapper


def get_export_conditions():
    return RecordExportMapper.get_export_conditions()


def export_records_to_docx(records, export_dir="exports", conditions=None):
    return RecordExportMapper.export_to_docx(records, export_dir, conditions)


def get_all_word_files():
    return WordFileMapper.find_all_ordered()


def get_word_file_by_id(file_id):
    return WordFileMapper.find_by_id(file_id)
