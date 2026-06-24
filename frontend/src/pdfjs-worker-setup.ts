import { pdfjs } from "react-pdf";

// Configure PDF.js worker for react-pdf (align with pdfjs-dist@5.x)
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  "pdfjs-dist/build/pdf.worker.min.mjs",
  import.meta.url,
).toString();
