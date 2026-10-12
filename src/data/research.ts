// Based on the CV supplied by Arash in October 2026.
// Hardware experiments and emulation-based trace checks are described separately.
export const research = [
  {
    id: "constant-time",
    period: "2025–present",
    topic: "Timing side channels & cryptographic software",
    title: "Constant-time cryptography on TrustZone-M",
    description:
      "Developing and evaluating a constant-time defence for modular inversion affected by CVE-2025-54764, with a focus on the M-Step timing side channel on Cortex-M33.",
    tools: ["Arm Cortex-M33", "Trusted Firmware-M", "Mbed TLS", "QEMU"],
    methods:
      "Firmware experiments on an STM32L552 board under Trusted Firmware-M, alongside instruction-trace comparisons using a QEMU plugin. The study examines secret-dependent control flow and the cost of the defence in the evaluated implementation.",
    paper: "https://doi.org/10.21203/rs.3.rs-10247338/v1",
    repository: null,
  },
  {
    id: "attestation",
    period: "2026",
    topic: "Remote attestation & bus-master isolation",
    title: "State authenticity beyond the CPU",
    description:
      "Investigating how non-secure DMA can alter attested state in a TrustZone-M proof-of-execution scheme, and evaluating a mitigation based on DMA channel security configuration.",
    tools: ["TrustZone-M", "STM32L5", "DMA", "Remote attestation"],
    methods:
      "A study of the SLAPP reference implementation on NUCLEO-L552ZE-Q, examining the check-then-commit window and validating DMA security configuration at the register level. The preprint describes the threat model, experiment and mitigation scope.",
    paper: "https://doi.org/10.21203/rs.3.rs-10521614/v1",
    repository:
      "https://github.com/Arash-devops/trustzone-dma-state-authenticity",
  },
];
export const publications = [
  {
    year: "2026",
    type: "Preprint",
    title:
      "State Authenticity under Multiple Bus Masters: A Non-Secure DMA Gap and Mitigation for TrustZone-M Proofs of Execution",
    authors: "Arash Razban",
    venue: "Research Square · Version 1",
    doi: "10.21203/rs.3.rs-10521614/v1",
  },
  {
    year: "2026",
    type: "Preprint",
    title:
      "Retrofit or Redesign? Hardware-Validated Constant-Time Defense and Cost Analysis for the M-Step Side-Channel on TrustZone-M",
    authors: "Arash Razban",
    venue: "Research Square · Version 1",
    doi: "10.21203/rs.3.rs-10247338/v1",
  },
  {
    year: "2016",
    type: "Conference paper",
    title:
      "Segmentation of retinal blood vessels by means of 2D Gabor wavelet and fuzzy mathematical morphology",
    authors: "A. Razban, K. Mahjoory and M. Nooshyar",
    venue:
      "2nd International Conference of Signal Processing and Intelligent Systems (ICSPIS) · pp. 1–5",
    doi: "10.1109/ICSPIS.2016.7869877",
  },
];
export const education = [
  {
    title: "MSc Cyber Security",
    institution: "IU International University of Applied Sciences, Berlin",
    period: "2025–present",
    current: true,
    note: null,
  },
  {
    title: "MSc Data Science",
    institution: "Ulster University, Northern Ireland, United Kingdom",
    period: "2022–2023",
    current: false,
    note: "Graduated with Distinction",
  },
  {
    title: "MSc Computer Hardware Engineering",
    institution: "Ardabil Public University, Iran",
    period: "2016–2018",
    current: false,
    note: null,
  },
];
