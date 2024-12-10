import BrowserPrint from "browserprint-es";
import { Notify } from "quasar";
import { useI18n } from "vue-i18n";

const { t: $t } = useI18n();

export function printProductLabel(productCode, productDescription) {
  const zpl = `
    ^XA
    ^CI28

    ^FO35,35
    ^FB525,1,10,L,0
    ^A0,60
    ^FD${productCode}
    ^FS

    ^FO35,100
    ^BY3,3,
    ^BC, 60,N, , ,^FD${productCode}
    ^FS

    ^FO35,180
    ^FB500,3,7,L,0
    ^A1,20
    ^FD${productDescription}
    ^FS

    ^XZ
  `;
  sendZplToPrinter(zpl);
}

export function printPositionLabel(position) {
  const zpl = `
    ^XA

    ^FO,54
    ^FS
    ^FT25,69
    ^AAN,50,27
    ^FH\
    ^FD${position}^FS

    ^BY2,2.1,110
    ^FT30,210
    ^B3N,N,,N,N
    ^FD${position}^FS

    ^PQ1,0,1,Y

    ^XZ
  `
  sendZplToPrinter(zpl);
}


export function postZPL(content, ip_addr) {
  var url = "http://"+ip_addr+"/pstprnt";
  var method = "POST";
  var async = true;
  var request = new XMLHttpRequest();

  request.open(method, url, async);
  request.setRequestHeader("Content-Type", content.type);

  // Actually sends the request to the server.
  request.send(content.value);
}

async function getPrinter() {
  console.log('Fetching default printer...')
  try {
    return await BrowserPrint.getDefaultDeviceAsync('printer')
  }
  catch (error) {
    Notify.create({
      type: 'negative',
      color: 'theme-red',
      message: $t('alerts.no_printer_found'),
      position: 'top'
    })
    return;
  }
}

export async function sendZplToPrinter(zpl) {
  const device = await getPrinter()
  device.send(zpl,
    (resp) => console.log(resp),
    (error) => {
      Notify.create({
        type: 'negative',
        color: 'theme-red',
        message: 'ERROR: ' + error,
        position: 'top'
      })
    }
  )
}

export async function sendPdfToPrinter(pdfData) {
  const device = await getPrinter()

  const blob = new Blob([pdfData], { type: 'application/pdf'}) // try this one too
  const url = URL.createObjectURL(blob)

  console.log('Sending the file to the printer...')
  device.sendFile(url,
    (response) => console.log(response),
    (error) => {
      Notify.create({
        type: 'negative',
        color: 'theme-red',
        message: 'ERROR: ' + error,
        position: 'top'
      })
    }
  );
}
