import { saveAs } from 'file-saver';
import * as XLSX from 'xlsx';

export function XLSXGetData(rows, columns) {
  return rows.map((entry) => {
    let row = {};
    columns.map((col) => {
      if (col.format) {
        row[col.label] = col.format(entry[col.field], entry);
      } else {
        row[col.label] = entry[col.field];
      }
    });
    return row;
  });
}

export function XLSXDownload(data, sheetName, fileName) {
  function s2ab(s) {
    var buf = new ArrayBuffer(s.length);
    var view = new Uint8Array(buf);
    for (var i = 0; i !== s.length; ++i) {
      view[i] = s.charCodeAt(i) & 0xff;
    }
    return buf;
  }

  if (!data) {
    return;
  }

  const wb = XLSX.utils.book_new();
  const ws = XLSX.utils.json_to_sheet(data);

  XLSX.utils.book_append_sheet(wb, ws, sheetName);

  const wbout = XLSX.write(wb, {
    bookType: 'xlsx',
    bookSST: false,
    type: 'binary',
  });
  saveAs(
    new Blob([s2ab(wbout)], {
      type: 'application/octet-stream',
    }),
    `${fileName}.xlsx`,
  );

  return XLSXDownload;
}
