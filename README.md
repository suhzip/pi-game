# Sky Pop — Week 2 (모듈 분리 버전)

Raspberry Pi + Adafruit 1.3-inch TFT Bonnet (240×240 ST7789)

## 실행
기존 라즈베리파이 프로젝트 폴더에 이 압축 파일의 내용을 복사한다.
기존 가상환경을 사용한다. 새로운 라이브러리는 필요하지 않다.

```bash
cd ~/pi-game
source ~/env/bin/activate
python -u game.py
```

SPI 16 MHz 테스트 (화면 이상 시 위 기본 실행으로 복귀):
```bash
SKYPOP_SPI_HZ=16000000 python -u game.py
```

## 파일별 역할
| 파일 | 내용 |
|---|---|
| game.py | 실행 진입점, SkyPop 객체, 게임 루프, 카메라/최고 높이 관리 |
| config.py | 속도, 점프, 구름 크기, 감전, 스테이지, LCD 설정 |
| player.py | Player: 이동, 중력, 점프, 감전, 새 피격, 그림 |
| cloud.py | Cloud: 개별 구름, CloudField: 생성/이동/착지/스크롤, 픽셀 그림 캐시 |
| enemy.py | Bird: 새 개체, EnemyManager: 생성/충돌/제거 |
| stage.py | StageManager: 시작/완료 안내, 게임 상태, 목표 및 진행률 |
| renderer.py | Renderer: 화면 합성, 배경, HUD, 시작/완료/게임오버 UI |
| display.py | Display: LCD 초기화 및 SPI 출력/종료 |
| joystick.py | Joystick: active-low GPIO 입력/종료 |
| test_game.py | unittest 기반 모의 로직 테스트 (실제 GPIO 없이 가능) |

## 주요 흐름
`game.py`에서 조이스틱 입력을 읽고 `Player.update()`를 호출한다.
`CloudField`에서 발판을 이동시키고 착지를 판정한다. 흰 구름은 `Player.bounce()`, 먹구름은 `Player.shock()`을 호출한다.
`EnemyManager`는 Stage 3의 새 충돌을 확인한다.
카메라와 최고 높이가 갱신되면 새 구름을 생성하고 `StageManager`가 화면 전환을 결정한다.
`Renderer`가 Pillow 이미지로 화면을 합성하고 `Display.show()`가 LCD로 전송한다.

## 난이도 조절
`config.py`: MOVE_SPEED=300, JUMP_POWER=-400, CLOUD_GAP=54, CLOUD_WIDTHS={1:46,2:40,3:36}.
스테이지 목표 높이는 500, 1000, 1500이다. STAGE_HEIGHT를 변경하면 FINAL_HEIGHT가 자동으로 3배가 된다.

## 테스트
```bash
python -m unittest -v
```
Pillow가 설치된 환경에서 실행 가능하다. 실제 LCD/GPIO 검증은 Raspberry Pi에서 실행하여 확인한다.
기존 game_platform.py는 사용하지 않는다. Python 표준 라이브러리와 충돌할 수 있으므로 platform.py라는 파일명은 피한다.
