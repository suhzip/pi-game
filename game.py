"""Sky Pop 실행 및 전체 게임 흐름 관리."""

import random
import time

from config import (
    H,
    JUMP_POWER,
    START_PLATFORM_Y,
    LANDING_OFFSET,
    MAX_LIVES,
    HIT_INVINCIBILITY
)

from joystick import Joystick

from display import (
    init_display,
    show_frame,
    close_display
)

from player import (
    update_player,
    take_damage
)

from cloud import (
    make_cloud,
    cloud_sprite,
    add_cloud_row,
    move_clouds,
    handle_landing,
    scroll_clouds
)

from enemy import update_birds

from stage import (
    show_banners,
    update_banner,
    check_stage
)

from renderer import (
    init_renderer,
    render
)


class SkyPop:

    # =========================
    # 게임 초기화
    # =========================
    def __init__(self):

        # 하드웨어 및 화면 초기화
        init_display(self)
        self.joy = Joystick()
        init_renderer(self)

        # 게임 상태
        self.state = "TITLE"
        self.highest = 0
        self.camera_y = 0.0

        # 캐릭터 상태
        self.px = 120.0
        self.py = 195.0
        self.vy = 0.0

        # 구름 상태
        self.clouds = []
        self.next_x = 120.0

        # 스테이지 상태
        self.stage = 1
        self.banners = []
        self.banner_left = 0.0

        # 새 장애물 상태
        self.birds = []
        self.bird_timer = 0.0

        # 목숨 및 피격 상태
        self.lives = MAX_LIVES
        self.hit_timer = 0.0

        # 추락 시 중복 피해 방지
        self.fall_damage_taken = False

        # 구름 이미지 미리 생성
        for kind, width in (
            ("normal", 64),
            ("storm", 64),
            ("normal", 90)
        ):

            cloud_sprite(kind, width)


    # =========================
    # 게임 시작 및 재시작
    # =========================
    def reset(self):

        self.state = "PLAY"

        # 캐릭터 초기화
        self.px = 120.0
        self.py = 195.0
        self.vy = JUMP_POWER

        # 카메라 및 높이 초기화
        self.camera_y = 0.0
        self.highest = 0
        self.next_x = 120.0

        # 첫 번째 구름 생성
        self.clouds = [
            make_cloud(120, 214, moving=False)
        ]

        # 초기 구름 생성
        for y in (152, 90, 28, -34, -96):

            x = max(
                44.0,
                min(
                    196.0,
                    self.next_x + random.randint(-38, 38)
                )
            )

            add_cloud_row(self, x, y)

        # 스테이지 초기화
        self.stage = 1

        # 장애물 초기화
        self.birds = []
        self.bird_timer = 0.0

        # 목숨 초기화
        self.lives = MAX_LIVES
        self.hit_timer = 0.0
        self.fall_damage_taken = False

        # Stage 1 시작 안내
        show_banners(self, [(1, "START")])


    # =========================
    # 캐릭터 부활
    # =========================
    def respawn(self):

        # 현재 화면에 있는 안전한 일반 구름 찾기
        safe_clouds = [
            cloud for cloud in self.clouds
            if cloud["kind"] == "normal"
            and 45 <= cloud["y"] - self.camera_y <= H - 30
        ]

        if safe_clouds:

            # 화면 아래쪽에 가까운 일반 구름 선택
            cloud = max(
                safe_clouds,
                key=lambda c: c["y"]
            )

        else:

            # 안전한 구름이 없으면 임시 구름 생성
            cloud = make_cloud(
                120,
                self.camera_y + 190,
                moving=False
            )

            self.clouds.append(cloud)

        # 캐릭터를 안전한 구름 위로 이동
        self.px = cloud["x"]

        self.py = cloud["y"] - LANDING_OFFSET

        # 자동 점프
        self.vy = JUMP_POWER

        # 부활 직후 무적 효과
        self.hit_timer = HIT_INVINCIBILITY

        # 낙하 피해 기록 초기화
        self.fall_damage_taken = False

        # 게임 진행 상태 유지
        self.state = "PLAY"

        print(
            f"RESPAWN! LIVES: {self.lives}",
            flush=True
        )


    # =========================
    # 게임 상태 갱신
    # =========================
    def update(self, dt):

        # 피격 후 무적 시간 감소
        self.hit_timer = max(
            0.0,
            self.hit_timer - dt
        )

        # 캐릭터 이동 및 물리 계산
        old_x, old_y, old_feet, new_feet = update_player(
            self, dt
        )

        # 구름 이동
        move_clouds(self, dt)

        # 구름 착지 및 충돌 판정
        handle_landing(
            self,
            old_feet,
            new_feet
        )

        # 먹구름 충돌로 목숨이 0개인 경우
        if self.state == "GAMEOVER":
            return

        # 새 장애물 이동 및 충돌 판정
        update_birds(
            self,
            dt,
            old_x,
            old_y
        )

        # 새 충돌로 목숨이 0개인 경우
        if self.state == "GAMEOVER":
            return

        # 카메라 수직 스크롤
        if self.py - self.camera_y < 88:

            self.camera_y = self.py - 88

        # 최고 도달 높이 기록
        self.highest = max(
            self.highest,
            int(
                START_PLATFORM_Y
                - (self.py + LANDING_OFFSET)
            )
        )

        # 신규 구름 생성 및 제거
        scroll_clouds(self)

        # =========================
        # 화면 아래로 추락한 경우
        # =========================
        if self.py - self.camera_y > H + 15:

            # 이번 낙하 중 먹구름이나 새에 의해
            # 이미 목숨이 감소했다면 추가 차감하지 않음
            if not self.fall_damage_taken:

                # 추락 피해는 무적 상태와 별도로 처리
                self.hit_timer = 0.0

                take_damage(self, "FALL")

            # 목숨이 모두 사라진 경우
            if self.lives <= 0:

                self.state = "GAMEOVER"

            else:

                # 목숨이 남아 있으면 현재 스테이지에서 부활
                self.respawn()

            return

        # 스테이지 진행 상태 확인
        check_stage(self)


    # =========================
    # 화면 렌더링 및 LCD 출력
    # =========================
    def render(self):

        render(self)

        show_frame(self)


    # =========================
    # 메인 게임 루프
    # =========================
    def run(self):

        previous_any = False
        previous_center = False

        last = time.monotonic()

        try:

            while True:

                now = time.monotonic()

                elapsed = now - last

                dt = min(elapsed, 0.06)

                last = now

                # 조이스틱 입력 확인
                any_pressed = any(
                    self.joy.pressed(k)
                    for k in (
                        "up",
                        "down",
                        "left",
                        "right",
                        "center"
                    )
                )

                center = self.joy.pressed("center")

                # 게임 시작
                if (
                    self.state == "TITLE"
                    and any_pressed
                    and not previous_any
                ):

                    self.reset()

                # 게임 진행
                elif self.state == "PLAY":

                    self.update(dt)

                # 스테이지 시작 및 종료 안내
                elif self.state == "BANNER":

                    update_banner(self, elapsed)

                # 게임 재시작
                elif (
                    self.state in ("GAMEOVER", "CLEAR")
                    and center
                    and not previous_center
                ):

                    self.reset()

                previous_any = any_pressed

                previous_center = center

                # 화면 출력
                self.render()

                time.sleep(0.005)

        except KeyboardInterrupt:

            print("Sky Pop stopped", flush=True)

        finally:

            # 하드웨어 자원 해제
            self.joy.close()

            close_display(self)


# =========================
# 프로그램 실행
# =========================
if __name__ == "__main__":

    SkyPop().run()