# Thành phần bên thứ ba — NumberTyper Preview

Danh mục này dựa trên bản dựng Windows preview ngày 2026-10-21. Các gói Python được đối chiếu với `build/windows/NumberTyper/Analysis-00.toc` và metadata trong môi trường dựng `.venv`; đây là kiểm kê kỹ thuật, không phải ý kiến pháp lý. Chưa thể coi đây là SBOM hoàn chỉnh vì một số DLL native, thành phần được liên kết tĩnh và model chưa có đủ notice/giấy phép của đúng tệp.

## Các gói Python có trong bản app

| Thành phần | Phiên bản | Giấy phép khai báo trong metadata | Nguồn |
|---|---:|---|---|
| annotated-types | 0.8.0 | MIT | [PyPI](https://pypi.org/project/annotated-types/) |
| certifi | 2026.10.18 | MPL-2.0 | [PyPI](https://pypi.org/project/certifi/) |
| cffi | 2.1.1 | MIT-0 | [PyPI](https://pypi.org/project/cffi/) |
| charset-normalizer | 3.5.2 | MIT | [PyPI](https://pypi.org/project/charset-normalizer/) |
| colorama | 0.4.6 | BSD (metadata chưa nêu SPDX cụ thể) | [PyPI](https://pypi.org/project/colorama/) |
| idna | 3.20 | BSD-3-Clause | [PyPI](https://pypi.org/project/idna/) |
| keyboard | 0.13.5 | MIT | [PyPI](https://pypi.org/project/keyboard/) |
| NumPy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 | [PyPI](https://pypi.org/project/numpy/) |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause | [PyPI](https://pypi.org/project/packaging/) |
| pycparser | 3.11 | BSD-3-Clause | [PyPI](https://pypi.org/project/pycparser/) |
| Pydantic | 2.14.1 | MIT | [PyPI](https://pypi.org/project/pydantic/) |
| pydantic-core | 2.50.1 | MIT | [PyPI](https://pypi.org/project/pydantic-core/) |
| PyYAML | 6.0.3 | MIT | [PyPI](https://pypi.org/project/PyYAML/) |
| Requests | 2.34.2 | Apache-2.0 | [PyPI](https://pypi.org/project/requests/) |
| setuptools | 84.2.1 | MIT | [PyPI](https://pypi.org/project/setuptools/) |
| sherpa-onnx | 1.13.8 | Apache-2.0 | [GitHub](https://github.com/k2-fsa/sherpa-onnx) |
| sherpa-onnx-core | 1.13.8 | Apache-2.0 | [GitHub](https://github.com/k2-fsa/sherpa-onnx) |
| SoundCard | 0.4.6 | BSD-3-Clause | [GitHub](https://github.com/bastibe/SoundCard) |
| srt | 3.5.3 | MIT | [PyPI](https://pypi.org/project/srt/) |
| tqdm | 4.70.1 | MPL-2.0 AND MIT | [PyPI](https://pypi.org/project/tqdm/) |
| typing-inspection | 0.4.4 | MIT | [PyPI](https://pypi.org/project/typing-inspection/) |
| typing_extensions | 4.16.0 | PSF-2.0 | [PyPI](https://pypi.org/project/typing-extensions/) |
| urllib3 | 2.8.0 | MIT | [PyPI](https://pypi.org/project/urllib3/) |
| Vosk Python | 0.3.45 | Apache-2.0 theo upstream; metadata wheel ghi `UNKNOWN` | [alphacep/vosk-api](https://github.com/alphacep/vosk-api) |
| websockets | 17.2 | BSD-3-Clause | [PyPI](https://pypi.org/project/websockets/) |

Các giấy phép trong bảng là khai báo của metadata upstream, chưa thay thế việc lưu bản văn license/notices của từng gói vào bản phân phối. Gói Vosk Python có trong app nhưng **không kèm Vosk model**.

## Model và thư viện native

| Thành phần trong gói | Nguồn / giấy phép đã tìm thấy | Trạng thái rà soát |
|---|---|---|
| Zipformer-VI: `encoder.int8.onnx`, `decoder.onnx`, `joiner.int8.onnx`, `tokens.txt` | [Tài liệu model và archive tải chính thức](https://github.com/k2-fsa/sherpa/blob/master/docs/source/onnx/pretrained_models/offline-transducer/zipformer-transducer-models.rst) dẫn tới [model card hynt](https://huggingface.co/hynt/Zipformer-30M-RNNT-6000h), khai báo CC BY-NC-ND 4.0 | Quyền của các tệp trong archive đã được liên hệ tới model card upstream; cần chủ sở hữu xác nhận quyền phân phối các tệp ONNX cụ thể. Không phát hành thương mại với model này nếu chưa có chấp thuận phù hợp. |
| Silero VAD `silero_vad.onnx` | Tải từ [release của sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/silero_vad.onnx); dự án [Silero VAD](https://github.com/snakers4/silero-vad) công bố MIT | Cần lưu bằng chứng quyền áp dụng cho đúng tệp model release và notice đi kèm. |
| sherpa C/C++ API và Python native extension | [k2-fsa/sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx), Apache-2.0 | DLL/extension đã thấy trong bundle; chưa đối chiếu đầy đủ các thư viện được liên kết tĩnh và third-party notices của bản Windows wheel. |
| ONNX Runtime `onnxruntime.dll` | [Microsoft ONNX Runtime](https://github.com/microsoft/onnxruntime), MIT | Đã nhận diện DLL trong bundle; phiên bản chính xác được sherpa-onnx-core đóng kèm và notice tương ứng chưa được chốt. |
| Vosk `libvosk.dll` | [alphacep/vosk-api](https://github.com/alphacep/vosk-api), Apache-2.0 theo upstream | Cần kiểm kê thư viện liên kết và notices của đúng wheel Windows. |
| NumPy/OpenBLAS DLL | NumPy khai báo nhiều giấy phép; [OpenBLAS](https://github.com/OpenMathLib/OpenBLAS) công bố BSD-3-Clause | DLL có trong bundle; cần xác minh phiên bản/build cụ thể và giữ đủ notices của các phần được liên kết. |
| Python `python314.dll`, Tcl/Tk, OpenSSL, zlib và runtime Windows | [Python license/acknowledgements](https://docs.python.org/3.14/license.html); OpenSSL 3 công bố Apache-2.0 | Bản app chứa các runtime này. Chưa đối chiếu hết phiên bản, license file và acknowledgements của mọi thành phần được Python build kèm. |
| `libgcc_s_seh-1.dll`, `libstdc++-6.dll`, `libwinpthread-1.dll` | Được phân phối trong cây thư viện của gói Vosk | Chưa xác minh phiên bản, license exception và bộ notice/source tương ứng; là cổng mở trước phân phối. |

## Thành phần dùng để dựng

| Công cụ | Phiên bản | Giấy phép / nguồn |
|---|---:|---|
| PyInstaller | 6.20.0 | GPL-2.0 với ngoại lệ cho ứng dụng đóng gói; một số tệp Apache-2.0. Xem [giải thích license upstream](https://github.com/pyinstaller/pyinstaller/blob/v6.20.0/doc/license.rst). |
| NSIS | 3.13 | Bản dựng dùng compressor zlib; [NSIS license](https://nsis.sourceforge.io/Docs/AppendixI.html) nêu mã nguồn/UI và module nén theo giấy phép riêng. Cần giữ đúng notice cho output installer. |

PyInstaller và NSIS là công cụ dựng; các component/runtime được nhúng trong artifact vẫn phải rà riêng. Extension Chromium trong gói do dự án viết, không có dependency npm bên thứ ba trong bản ZIP hiện tại.

## Những gì đã được loại khỏi app Windows

Bản app chỉ dùng Chromium extension bridge; nhóm legacy desktop automation không cần cho entry point này đã được loại khỏi bundle: PyAutoGUI cùng `MouseInfo`, `PyMsgBox`, `PyGetWindow`, `PyScreeze`, `Pyperclip`, `PyRect` và `pytweening`. Các module sender cũ vẫn còn trong source tree/môi trường phát triển. Việc loại khỏi bản app được đối chiếu qua PyInstaller Analysis mới ngày 2026-10-21. Đặc biệt, PyPI hiện khai báo `MouseInfo` và `PyMsgBox` GPLv3+; do đó chúng không còn nằm trong app bundle này.

## Điều kiện trước khi phát hành

- Tạo SBOM có thể tái lập từ chính installer cuối, gồm cả gói Python, binary/native closure, runtime và model; đối chiếu lại sau mỗi lần dựng.
- Đưa bản văn license/notice bắt buộc vào artifact cài đặt, không chỉ giữ một bảng tổng hợp.
- Xác nhận quyền phân phối của đúng Zipformer ONNX và Silero ONNX; model card Zipformer ghi CC BY-NC-ND 4.0 nên bản preview hiện tại chỉ dành cho thử nghiệm cá nhân phi thương mại theo phạm vi đã công bố. Không gọi đây là giấy phép phát hành thương mại.
- Xác minh đầy đủ third-party notices cho sherpa/ONNX Runtime, Vosk/GCC runtimes, OpenBLAS, Python/OpenSSL/Tcl/Tk và NSIS installer.

Vì các mục trên chưa xong, M2 trong sprint P1 vẫn **một phần**, và installer hiện tại vẫn là preview cục bộ, chưa đủ điều kiện phát hành công khai.
