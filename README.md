# ZTF DR2 Light-Curve Downloader

이 저장소에는 IRSA에서 ZTF DR2 light-curve 자료를 대량으로 내려받아
`sncosmo` 등에서 사용할 수 있는 `astropy.table.Table` 형식으로 저장하는
파이썬 스크립트가 포함되어 있습니다.

## 준비물

1. [IRSA 계정](https://irsa.ipac.caltech.edu/account/applications.html)과
   "ZTF Light Curve Access" 권한
2. 파이썬 3.9 이상

선행 라이브러리는 미리 만들어 둔 가상환경 `snpy1`을 활성화한 뒤 설치하면 됩니다.

```bash
source snpy1/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

> **requirements.txt가 없다고 나올 때는?**
> 1. `requirements.txt` 파일이 있는 폴더(보통 이 저장소의 루트) 안에서 명령을 실행했는지 `ls`로 확인합니다.
> 2. 저장소 전체를 복사하지 않고 `download_ztf_lightcurves.py`만 따로 옮겨 둔 경우에는 아래 명령으로 `requirements.txt`를 직접 만들어 같은 위치에 두세요.
>    ```bash
>    cat <<'EOF' > requirements.txt
>    astroquery>=0.4.7
>    astropy>=5.0
>    EOF
>    ```
> 3. 그래도 설치가 어렵다면 `pip install astroquery>=0.4.7 astropy>=5.0`처럼 직접 패키지 이름을 지정해 설치해도 됩니다.

필요하다면 아래 스크립트를 이용해 한 번에 설치할 수도 있습니다.

```bash
cat <<'EOF' > install_prereqs.sh
#!/usr/bin/env bash
set -euo pipefail
source snpy1/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
EOF
chmod +x install_prereqs.sh
./install_prereqs.sh
```

## GitHub와 Bash 처음부터 따라 하기

GitHub나 터미널(Bash)이 처음이라면 아래 순서를 차례로 진행하세요.

1. **GitHub 계정 만들기**
   - [https://github.com/join](https://github.com/join)으로 이동해 계정을 생성합니다.
   - 이메일 인증까지 완료해야 저장소를 복제(clone)할 수 있습니다.

2. **Git 설치하기 (Ubuntu 기준)**
   ```bash
   sudo apt update
   sudo apt install -y git
   ```

3. **터미널 기본 명령 연습**
   - `pwd`: 현재 작업 중인 폴더의 전체 경로를 확인합니다.
   - `ls`: 현재 폴더 안의 파일과 폴더 목록을 확인합니다.
   - `cd 폴더이름`: 해당 폴더로 이동합니다. 예) `cd Desktop`
   - `cd ..`: 한 단계 상위 폴더로 이동합니다.
   - `mkdir 폴더이름`: 새 폴더를 만듭니다.

4. **저장소 복제(clone)**
   - 터미널에서 작업할 위치(예: 바탕화면)로 이동합니다.
     ```bash
     cd ~/Desktop
     ```
   - 아래 명령에서 `본인깃허브아이디`를 실제 GitHub 사용자 이름으로 바꿔 입력합니다.
     ```bash
     git clone https://github.com/본인깃허브아이디/silverdgx.git
     ```
   - 위 저장소가 **공개(public)**라면 추가 입력 없이 바로 복제됩니다. 만약 조직용 저장소처럼 **비공개(private)** 상태이거나, HTTPS로 복제할 때 아이디·비밀번호를 묻는 메시지가 나오면 아래 절차로 [Personal Access Token(PAT)](https://github.com/settings/tokens) 을 준비해야 합니다.
     1. GitHub 우측 상단 아바타 → **Settings** → **Developer settings** → **Personal access tokens**로 이동합니다.
     2. **Fine-grained token** 또는 **classic token**을 생성하고, `repo` 권한을 부여합니다.
     3. 터미널에서 다음과 같이 토큰을 함께 넣어 복제합니다 (`토큰값` 부분은 실제 생성된 토큰 문자열로 교체).
        ```bash
        git clone https://본인깃허브아이디:토큰값@github.com/본인깃허브아이디/silverdgx.git
        ```
     4. 토큰을 직접 노출하기 부담된다면 `git config --global credential.helper store`로 자격 증명을 저장하거나, [GitHub CLI(gh)](https://cli.github.com/)를 설치해 `gh auth login`으로 로그인한 뒤 `gh repo clone 본인깃허브아이디/silverdgx`처럼 사용할 수도 있습니다.
   - 복제가 끝나면 `cd silverdgx`로 들어갑니다.

   > **참고: 저장소를 공개(public)로 전환하려면?**
   > 1. GitHub 웹사이트에서 해당 저장소 페이지로 이동합니다.
   > 2. 상단 메뉴에서 **Settings**를 클릭합니다.
   > 3. 좌측 사이드바 하단의 **Danger Zone** 섹션으로 내려갑니다.
   > 4. **Change repository visibility** 항목의 **Change visibility** 버튼을 누릅니다.
   > 5. `Make this repository public`를 선택하고, 안내에 따라 저장소 이름을 입력해 확인을 완료합니다.
   >    - 조직(Organization) 소유 저장소인 경우, 관리자의 승인 단계가 추가될 수 있습니다.
   > 6. 마지막으로 **I understand, change repository visibility**를 클릭하면 저장소가 공개로 전환됩니다.
   > 7. 이후 `git remote -v`로 원격 주소를 확인하고, 필요 시 기존에 복제한 로컬 저장소는 그대로 사용하거나 새로 복제하면 됩니다.

5. **가상환경 활성화 및 라이브러리 설치**
   ```bash
   source snpy1/bin/activate
   pip install -r requirements.txt
   ```

6. **스크립트 실행**
   - Type Ia 초신성 데이터를 모두 받고 싶다면 아래처럼 실행합니다.
     ```bash
     ./run_sn_type_ia.sh --username <IRSA_ID>
     ```
   - 혹은 직접 스크립트를 호출할 수도 있습니다.
     ```bash
     python download_ztf_lightcurves.py --sn-type-ia --username <IRSA_ID>
     ```

7. **다운로드 결과 확인**
   - 모든 결과는 자동으로 `~/Desktop/ztf_lightcurves` 폴더에 저장됩니다.
   - `ls ~/Desktop/ztf_lightcurves`로 저장된 `.ecsv` 파일을 확인할 수 있습니다.

8. **로컬에서 바꾼 내용을 GitHub에 올리기 (push)**
   - GitHub 웹사이트의 README가 갱신되지 않는다면, 로컬에서 수정한 내용을 아직 `push`하지 않은 것입니다.
   - 우선 현재 변경 사항을 확인합니다.
     ```bash
     git status
     ```
   - 업로드할 파일을 선택해 스테이징합니다. (예: README와 스크립트를 수정했다면)
     ```bash
     git add README.md download_ztf_lightcurves.py
     ```
     > 여러 파일을 모두 올리고 싶다면 `git add .`으로 현재 폴더 전체를 선택할 수도 있습니다.
   - 변경 내용에 대한 메시지를 붙여 커밋을 만듭니다. 처음 커밋한다면 사용자 이름/이메일을 설정하라는 메시지가 나올 수 있으며, 안내에 따라 `git config --global user.name "이름"` 등을 입력하면 됩니다.
     ```bash
     git commit -m "문서: README 한글 가이드 갱신"
     ```
   - 마지막으로 원격 저장소(예: GitHub)의 기본 브랜치로 푸시합니다. 기본 브랜치가 `main`이 아니라면 해당 이름으로 바꿔 입력하세요.
     ```bash
     git push origin main
     ```
   - `git push`가 성공적으로 끝나면 몇 초 뒤 GitHub 웹 페이지를 새로 고침했을 때 변경된 README가 그대로 표시됩니다.

## 사용 방법

### 빠른 시작 (Ubuntu 기준)

```bash
# 아래에서 "본인깃허브아이디"를 실제 GitHub 사용자 이름으로 바꿔 주세요.
git clone https://github.com/본인깃허브아이디/silverdgx.git
# 예: git clone https://github.com/astro-user/silverdgx.git
# 저장소가 비공개이거나 인증을 요구하면 아래처럼 Personal Access Token을 함께 사용하세요.
# git clone https://본인깃허브아이디:토큰값@github.com/본인깃허브아이디/silverdgx.git
cd silverdgx
ls requirements.txt  # 파일이 존재하는지 먼저 확인
source snpy1/bin/activate
pip install -r requirements.txt
./run_sn_type_ia.sh --username <IRSA_ID>
```

첫 실행 시 IRSA 비밀번호를 입력하라는 메시지가 나오며, 모든 Type Ia
초신성(objectid 목록을 TAP 쿼리로 자동 추출)이 순차적으로 내려받힙니다.
실행 디렉터리는 자유롭게 선택할 수 있으며, 결과 파일은 항상
`~/Desktop/ztf_lightcurves` 아래에 저장됩니다.

> 참고: 스크립트에 실행 권한을 부여하면 `./download_ztf_lightcurves.py`처럼
> 직접 실행할 수도 있습니다.

1. **특정 분류 전체를 내려받고 싶을 때** (예: 모든 Type Ia 초신성):

   ```bash
   ./run_sn_type_ia.sh --username <IRSA_ID>
   ```

   `--sn-type-ia`는 내부적으로 `ztf_objects_dr2.classification LIKE 'SN Ia%'`
   조건으로 TAP 쿼리를 실행하여 모든 Ia 및 Ia 하위형(objectid 기준)을
   가져온 뒤, 각 light-curve를 순차적으로 내려받습니다. 너무 많은 대상이
   한꺼번에 내려받히는 것이 부담스럽다면 `--limit 3500`처럼 상한을 줄 수
   있습니다.

   보다 일반적으로는 `--classification` 옵션에 SQL `LIKE` 패턴을 전달해
   다른 분류를 지정할 수 있습니다. 예를 들어 `--classification "SN Ib%"`
   또는 `--classification "AGN"`처럼 사용할 수 있습니다.

2. **이미 objectid 목록이 있다면** 텍스트 파일(예: `targets.txt`)로 한 줄에
   하나씩 정리하고, 아래와 같이 실행합니다.

   ```bash
   python download_ztf_lightcurves.py targets.txt --username <IRSA_ID>
   ```

   실행하면 IRSA 비밀번호를 입력하라는 메시지가 뜨며, 다운로드가
   진행됩니다. 기본적으로 결과는 바탕화면(`~/Desktop`) 아래의
   `ztf_lightcurves` 폴더에 `<objectid>.ecsv` 파일로 저장됩니다.

## 주요 옵션

- `--output`: 저장 경로를 직접 지정합니다.
- `--delay`: 각 요청 사이의 대기 시간을 초 단위로 지정합니다.
- `--max-attempts`: 요청 실패 시 재시도 횟수를 지정합니다.
- `--sn-type-ia`: ZTF DR2에서 Type Ia 초신성(하위형 포함) 전체를 자동으로
  내려받습니다.
- `--classification`: `ztf_objects_dr2.classification` 컬럼에 SQL `LIKE`
  패턴을 적용해 대상 목록을 자동 생성합니다.
- `--limit`: `--classification`이나 `--sn-type-ia` 사용 시 최대 대상 수를
  제한합니다.

`download_ztf_lightcurves.py --help`를 실행하면 전체 옵션을 확인할 수
있습니다.

## sncosmo에서 사용하기

저장된 `.ecsv` 파일은 아래와 같이 쉽게 불러와 `sncosmo` 피팅에 활용할
수 있습니다.

```python
from astropy.table import Table
import sncosmo

table = Table.read("~/Desktop/ztf_lightcurves/ZTF19abcd1234.ecsv", format="ascii.ecsv")

# 필요에 따라 필터/컬럼을 가공한 뒤 sncosmo.fit_lc에 전달합니다.
```

필요에 따라 필터 이름 매핑과 제로포인트 처리 등을 조정해 주면 됩니다.
