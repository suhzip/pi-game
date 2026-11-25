# ☁️ Sky Pop

**Raspberry Pi 기반 픽셀아트 수직 점프 게임**

한국항공대학교 | 임베디드 SW 프로젝트

## 1. 게임 소개

Sky Pop은 조이스틱으로 캐릭터를 조작하여 구름을 밟고 하늘 위로 올라가는 수직 스크롤 게임이다.

플레이어는 일반 구름을 밟으며 상승하고, 먹구름과 새 장애물을 피해 총 3개의 스테이지를 통과해야 한다.

Raspberry Pi와 TFT LCD를 기반으로 동작하며, Pygame 없이 게임 로직, 물리 계산, 충돌 판정 및 화면 출력을 직접 구현하였다.

## 2. 개발 환경

| 구분 | 사용 기술 |
|---|---|
| Hardware | Raspberry Pi 4 Model B |
| Display | Adafruit 1.3-inch TFT Bonnet (240 × 240) |
| OS | Raspberry Pi OS |
| Language | Python |
| Graphics | Pillow, Pixel Art PNG |
| Library | Adafruit Blinka, Adafruit RGB Display |
| Communication | GPIO, SPI |
| IDE | VS Code, Remote SSH |
| Version Control | Git, GitHub |

## 3. 게임 조작 방법

| 조작 | 기능 |
|---|---|
| LEFT / RIGHT | 캐릭터 좌우 이동 |
| 일반 구름 착지 | 자동 점프 |
| 먹구름 착지 | 목숨 감소 및 낙하 |
| 새 장애물 충돌 | 목숨 감소 및 강제 낙하 |
| 아무 버튼 | 게임 시작 |
| CENTER | 게임 재시작 |

## 4. 스테이지 구성

| Stage | Name | Height | 장애물 |
|---|---|---|---|
| Stage 1 | Sunny Sky | 0 ~ 1000 | 일반 구름 |
| Stage 2 | Cloud Trap | 1000 ~ 2000 | 일반 구름 및 먹구름 |
| Stage 3 | Danger Zone | 2000 ~ 3000 | 먹구름 및 새 장애물 |

최종 목표 높이인 3000에 도달하면 게임을 클리어한다.

## 5. 주요 기능

### Game System

- 조이스틱 기반 캐릭터 이동
- 중력, 낙하 및 자동 점프
- 구름의 무작위 생성 및 좌우 이동
- 수직 카메라 스크롤
- 스테이지별 배경 및 장애물 변경
- 높이 및 스테이지 진행률 표시
- START / FINISH / GAME OVER / GAME CLEAR 화면

### Life & Respawn System

- 기본 목숨 3개 제공
- 오른쪽 상단에 하트 UI 표시
- 먹구름, 새 장애물 충돌 및 추락 시 목숨 감소
- 피격 후 1초간 무적 및 캐릭터 깜빡임 효과
- 피격 이후 추락 시 중복 피해 방지
- 목숨이 남아 있으면 안전한 구름에서 부활
- 스테이지 전환 및 부활 시 게임 진행 상태 유지
- 목숨이 0개일 경우 게임 종료

### Pixel Art

![Player](assets/player.png)
![Normal Cloud](assets/cloud_normal.png)
![Storm Cloud](assets/cloud_storm.png)

캐릭터 및 장애물에 PNG 기반 픽셀아트 이미지를 적용하였다.

## 6. 프로젝트 파일 구조

```text
pi-game/
├── assets/
│   ├── cloud_normal.png  # 일반 구름 이미지
│   └── cloud_storm.png   # 먹구름 이미지
├── game.py              # 게임 실행 및 상태 관리
├── config.py            # 게임 설정값 및 상수
├── player.py            # 캐릭터 이동 및 피해 처리
├── cloud.py             # 구름 생성, 이동 및 충돌
├── enemy.py             # 장애물 생성, 이동 및 충돌
├── stage.py             # 스테이지 진행 관리
├── renderer.py          # 게임 그래픽 및 UI
├── display.py           # LCD 출력 및 SPI 통신
├── joystick.py          # GPIO 조이스틱 입력
├── main.py              # 초기 실행 파일
├── game_platform.py     # 초기 발판 구현 파일 (미사용)
├── .gitignore
└── README.md
```

## 7. 실행 방법

```bash
cd ~/pi-game
source ~/env/bin/activate
python -u game.py
```

게임 종료: `Ctrl + C`

## 8. 개발 진행 상황

### Week 1 — 기본 게임 구현

- [x] Raspberry Pi 개발 환경 구축
- [x] GPIO 및 SPI 통신
- [x] 조이스틱 입력 및 LCD 출력
- [x] 캐릭터 이동 및 자동 점프
- [x] 구름 생성 및 충돌 판정
- [x] 수직 스크롤 구현

### Week 2 — 게임 기능 확장

- [x] 코드 모듈화 및 리팩토링
- [x] 3단계 스테이지 구현
- [x] 먹구름 및 새 장애물 구현
- [x] 하트 기반 목숨 시스템
- [x] 피격 및 부활 시스템 코드 작성
- [x] 픽셀아트 구름 이미지 적용
- [x] 구름 크기 및 충돌 범위 조정
- [ ] 캐릭터 및 장애물 이미지 개선
- [ ] 스테이지별 배경 디자인
- [ ] 캐릭터 조작감 및 난이도 개선
- [ ] 아이템 및 점수 시스템
- [ ] 통합 테스트

### Week 3 — 최종 게임 완성

- [ ] 최종 보스전 구현
- [ ] 게임 UI 개선
- [ ] 성능 최적화
- [ ] 최종 게임 테스트
- [ ] 시연 영상 및 결과보고서 제작