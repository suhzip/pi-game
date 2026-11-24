# ☁️ Sky Pop

**Raspberry Pi 기반 임베디드 수직 점프 게임**

임베디드 SW 프로젝트 | 한국항공대학교

## 1. 프로젝트 소개

Sky Pop은 Raspberry Pi 4 Model B와 TFT LCD Bonnet을 활용한 수직 스크롤 방식의 점프 게임이다.

플레이어는 조이스틱을 이용하여 캐릭터를 좌우로 이동시키고, 구름을 밟으며 더 높은 곳으로 올라간다. 높이에 따라 스테이지가 변경되며, 먹구름과 움직이는 장애물이 등장하여 게임의 난이도가 점차 증가한다.

플레이어에게는 총 3개의 목숨이 주어지며, 장애물 충돌 및 추락으로 목숨이 감소한다.

Pygame과 같은 전용 게임 라이브러리를 사용하지 않고 게임 루프, 물리 계산, 충돌 판정, 그래픽 처리 및 하드웨어 제어를 직접 구현한다.

픽셀아트 기반의 게임 디자인을 적용하고, 이미지 리소스를 별도로 관리하여 그래픽의 완성도와 코드의 유지보수성을 높인다.

## 2. 개발 환경

| 구분 | 사용 기술 및 장비 |
|---|---|
| Hardware | Raspberry Pi 4 Model B |
| Display | Adafruit 1.3-inch TFT Bonnet |
| Display Controller | ST7789 |
| Resolution | 240 × 240 |
| OS | Raspberry Pi OS |
| Language | Python |
| Graphics | Pillow (PIL) |
| Graphic Assets | Pixel Art, Transparent PNG |
| Hardware Control | Adafruit Blinka |
| Display Library | Adafruit RGB Display |
| Communication | SPI, GPIO |
| IDE | Visual Studio Code |
| Remote Development | SSH, VS Code Remote SSH |
| Version Control | Git, GitHub |

### 사용 라이브러리

| Library | Description |
|---|---|
| Pillow | 이미지 로딩, 크기 조절, 그래픽 및 UI 렌더링 |
| board | Raspberry Pi GPIO 핀 및 SPI 인터페이스 접근 |
| digitalio | 조이스틱 GPIO 입력 및 LCD 제어 |
| adafruit_rgb_display | ST7789 LCD 초기화 및 화면 출력 |
| random | 구름 및 장애물 무작위 생성 |
| time | 게임 루프 및 시간 관리 |
| functools | 이미지 캐싱을 통한 연산 최적화 |
| pathlib | 외부 이미지 리소스의 파일 경로 관리 |

## 3. 게임 조작 및 진행 방법

| 조작 | 기능 |
|---|---|
| 조이스틱 LEFT | 캐릭터 왼쪽 이동 |
| 조이스틱 RIGHT | 캐릭터 오른쪽 이동 |
| 일반 구름 착지 | 자동 점프 |
| 먹구름 착지 | 목숨 감소 및 낙하 |
| 새 장애물 충돌 | 목숨 감소 및 강제 낙하 |
| 아무 버튼 | 게임 시작 |
| CENTER 버튼 | 게임 종료 후 재시작 |

캐릭터는 일반 구름에 착지하면 자동으로 점프하며, 플레이어는 좌우 이동을 통해 다음 구름에 착지해야 한다.

목숨이 남아 있다면 추락 이후 안전한 구름에서 부활할 수 있으며, 모든 목숨을 소진하면 게임이 종료된다.

## 4. 스테이지 구성

| Stage | 이름 | 높이 | 특징 |
|---|---|---|---|
| Stage 1 | Sunny Sky | 0 ~ 500 | 일반 구름 등장 |
| Stage 2 | Cloud Trap | 500 ~ 1000 | 일반 구름 및 먹구름 등장 |
| Stage 3 | Danger Zone | 1000 ~ 1500 | 먹구름 및 새 장애물 등장 |

- Stage 1: 기본 조작과 점프에 적응하는 단계
- Stage 2: 먹구름을 피하며 일반 구름에 착지하는 단계
- Stage 3: 움직이는 새와 먹구름을 동시에 피하는 단계

각 스테이지의 시작과 종료 시 START 및 FINISH 메시지를 표시한다.

최종 목표 높이인 1500에 도달하면 GAME CLEAR 화면이 출력된다.

## 5. 주요 구현 기능

### Character

- 조이스틱 기반 좌우 이동
- 중력을 적용한 점프 및 낙하
- 일반 구름 착지 시 자동 점프
- 화면 경계를 벗어나지 않도록 이동 범위 제한
- 장애물 충돌 시 캐릭터 깜빡임 효과

### Cloud

- 일반 구름 및 먹구름 구현
- 구름의 좌우 왕복 이동
- 무작위 구름 배치
- 캐릭터와 구름 사이의 충돌 판정
- 먹구름 착지 시 목숨 감소 및 낙하
- 화면 위쪽의 신규 구름 생성
- 화면 아래쪽으로 벗어난 구름 제거
- 외부 PNG 기반 픽셀아트 구름 디자인 적용
- 구름 가로 크기 64px에서 56px로 축소
- 변경된 구름 크기에 맞춘 충돌 범위 조정
- 투명 배경 이미지 합성
- 이미지 캐싱을 통한 반복 로딩 최소화

### Enemy

- Stage 3에서 새 장애물 등장
- 일정한 시간 간격으로 장애물 생성
- 화면 좌우를 가로지르는 장애물 이동
- 이동 방향에 따른 이미지 반전
- 캐릭터와 장애물의 충돌 판정
- 충돌 시 목숨 감소 및 강제 낙하

### Life & Respawn System

- 기본 목숨 3개 제공
- 화면 오른쪽 상단에 작은 픽셀아트 하트 3개 표시
- 남은 목숨은 빨간색, 잃은 목숨은 회색으로 표시
- 먹구름 및 새 장애물 충돌 시 목숨 1개 감소
- 피격 후 게임 시간 기준 1초간 무적 상태 적용
- 일반 추락 시 목숨 1개 감소
- 장애물 충돌 이후 추락 시 중복 피해 방지
- 목숨이 남아 있으면 안전한 일반 구름에서 부활
- 부활 시 현재 스테이지 및 최고 도달 높이 유지
- 스테이지 전환 시 남은 목숨 유지
- 목숨이 0개일 경우 GAME OVER
- 게임 재시작 시 목숨 3개로 초기화

### Stage & Game System

- 3단계 스테이지 시스템
- 최고 도달 높이 측정
- 스테이지 진행률 표시
- 스테이지별 배경 색상 변경
- Stage START / FINISH 안내
- 수직 카메라 스크롤
- GAME OVER 및 GAME CLEAR 화면
- 게임 재시작 기능

### Graphic Assets

일반 구름과 먹구름을 기존 코드 기반 도형 생성 방식에서 외부 PNG 이미지 리소스 방식으로 변경하였다.

| 일반 구름 | 먹구름 |
|:---:|:---:|
| ![Normal Cloud](assets/cloud_normal.png) | ![Storm Cloud](assets/cloud_storm.png) |
| 56 × 28 px | 56 × 44 px |
| 안전한 점프 발판 | 번개를 포함한 위험 발판 |

- 생성형 AI를 활용한 픽셀아트 이미지 제작
- RGBA 형식의 투명 배경 PNG 사용
- 240 × 240 LCD 해상도에 적합한 이미지 크기 적용
- Nearest Neighbor 방식으로 픽셀아트의 선명한 경계 유지
- 이미지 리소스와 게임 로직 분리
- assets 디렉터리를 통한 그래픽 리소스 관리

## 6. 임베디드 SW 구현 기술

### GPIO 입력 처리

Raspberry Pi의 GPIO 핀과 조이스틱을 연결