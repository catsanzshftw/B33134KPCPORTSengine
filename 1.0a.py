from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import math
import random
import tkinter as tk
from tkinter import ttk
import threading

# Initialize Ursina with 60 FPS target
app = Ursina(vsync=True, development_mode=False)
window.fps_counter.enabled = True
window.exit_button.visible = False
window.title = 'Mario 3D Land - B3313 Tech Demo'

# Atmospheric fog and lighting
scene.fog_color = color.rgb(25, 25, 45)
scene.fog_density = 0.05
camera.fov = 80

# Custom player controller with Mario-like physics
class MarioController(Entity):
    def __init__(self):
        super().__init__()
        self.speed = 8
        self.jump_height = 3
        self.jump_count = 0
        self.max_jumps = 2
        self.gravity = 40
        self.grounded = False
        self.velocity = Vec3(0, 0, 0)
        
        # Player model
        self.model = 'cube'
        self.color = color.rgb(200, 50, 50)
        self.scale = (1, 2, 1)
        self.position = (0, 5, 0)
        self.collider = BoxCollider(self, size=(1, 2, 1))
        
        # Camera setup
        camera.parent = self
        camera.position = (0, 8, -15)
        camera.rotation_x = 20
        
        # Movement smoothing
        self.target_rotation = 0
        self.rotation_speed = 10
        
    def update(self):
        # Smooth rotation
        self.rotation_y = lerp(self.rotation_y, self.target_rotation, time.dt * self.rotation_speed)
        
        # Movement input
        movement = Vec3(0, 0, 0)
        if held_keys['a']:
            movement.x -= 1
            self.target_rotation = -90
        if held_keys['d']:
            movement.x += 1
            self.target_rotation = 90
        if held_keys['w']:
            movement.z += 1
            self.target_rotation = 0
        if held_keys['s']:
            movement.z -= 1
            self.target_rotation = 180
            
        # Diagonal movement rotation
        if held_keys['w'] and held_keys['d']:
            self.target_rotation = 45
        elif held_keys['w'] and held_keys['a']:
            self.target_rotation = -45
        elif held_keys['s'] and held_keys['d']:
            self.target_rotation = 135
        elif held_keys['s'] and held_keys['a']:
            self.target_rotation = -135
            
        # Apply movement
        if movement.length() > 0:
            movement = movement.normalized() * self.speed
            self.velocity.x = movement.x
            self.velocity.z = movement.z
        else:
            self.velocity.x = lerp(self.velocity.x, 0, time.dt * 10)
            self.velocity.z = lerp(self.velocity.z, 0, time.dt * 10)
        
        # Gravity
        if not self.grounded:
            self.velocity.y -= self.gravity * time.dt
        
        # Jump
        if self.grounded:
            self.jump_count = 0
            
        if held_keys['space'] and self.jump_count < self.max_jumps:
            self.velocity.y = self.jump_height * 3
            self.jump_count += 1
            held_keys['space'] = False
        
        # Apply velocity
        self.position += self.velocity * time.dt
        
        # Ground check
        hit_info = raycast(self.world_position + Vec3(0, 0.1, 0), Vec3(0, -1, 0), distance=0.2)
        self.grounded = hit_info.hit
        
        if self.grounded and self.velocity.y < 0:
            self.velocity.y = 0

# Create player
player = MarioController()

# Satellite HUD using Canvas
class SatelliteHUD(Entity):
    def __init__(self):
        super().__init__()
        self.minimap = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(20, 20, 40, 200),
            scale=(0.3, 0.3),
            position=(-0.65, 0.35)
        )
        
        # Minimap border
        self.border = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgb(100, 100, 150),
            scale=(0.32, 0.32),
            position=(-0.65, 0.35),
            z=-0.01
        )
        
        # Player indicator
        self.player_dot = Entity(
            parent=camera.ui,
            model='circle',
            color=color.rgb(255, 100, 100),
            scale=(0.02, 0.02),
            position=(-0.65, 0.35),
            z=-0.02
        )
        
        # Level indicators
        self.level_dots = []
        
    def update(self):
        # Update player position on minimap
        map_scale = 0.005
        self.player_dot.position = (
            -0.65 + player.x * map_scale,
            0.35 + player.z * map_scale
        )
        
        # Update level object dots
        for i, obj in enumerate(level_objects):
            if i >= len(self.level_dots):
                dot = Entity(
                    parent=camera.ui,
                    model='circle',
                    color=color.rgb(100, 200, 100),
                    scale=(0.01, 0.01),
                    z=-0.02
                )
                self.level_dots.append(dot)
            
            self.level_dots[i].position = (
                -0.65 + obj.x * map_scale,
                0.35 + obj.z * map_scale
            )

# Create HUD
hud = SatelliteHUD()

# B3313-inspired level generation
level_objects = []

# Ground planes with varied heights
for x in range(-50, 50, 10):
    for z in range(-50, 50, 10):
        height = random.uniform(-2, 2) if random.random() > 0.7 else 0
        ground = Entity(
            model='cube',
            color=color.rgb(40, 40, 60) if height == 0 else color.rgb(60, 60, 80),
            scale=(10, 0.5, 10),
            position=(x, height, z),
            texture='white_cube',
            collider='box'
        )
        
# Mysterious floating platforms
for i in range(20):
    platform = Entity(
        model='cube',
        color=color.rgb(80, 50, 120),
        scale=(random.uniform(2, 6), 0.5, random.uniform(2, 6)),
        position=(
            random.uniform(-40, 40),
            random.uniform(5, 20),
            random.uniform(-40, 40)
        ),
        collider='box'
    )
    level_objects.append(platform)

# Liminal pillars
for i in range(15):
    pillar = Entity(
        model='cube',
        color=color.rgb(30, 30, 50),
        scale=(2, random.uniform(10, 30), 2),
        position=(
            random.uniform(-45, 45),
            0,
            random.uniform(-45, 45)
        ),
        collider='box'
    )

# Glowing orbs for atmosphere
orbs = []
for i in range(10):
    orb = Entity(
        model='sphere',
        color=color.rgb(100, 150, 255),
        scale=0.5,
        position=(
            random.uniform(-40, 40),
            random.uniform(3, 15),
            random.uniform(-40, 40)
        )
    )
    orb.unlit = True
    orbs.append(orb)

# Rotating mystery cubes
mystery_cubes = []
for i in range(5):
    cube = Entity(
        model='cube',
        color=color.rgb(255, 200, 100),
        scale=1.5,
        position=(
            random.uniform(-30, 30),
            random.uniform(5, 10),
            random.uniform(-30, 30)
        )
    )
    cube.unlit = True
    mystery_cubes.append(cube)

# Atmospheric skybox
class Sky(Entity):
    def __init__(self):
        super().__init__(
            parent=scene,
            model='sphere',
            scale=500,
            texture='white_cube',
            double_sided=True
        )
        self.color = color.rgb(10, 10, 30)

sky = Sky()

# Update functions
def update():
    # Animate orbs
    for i, orb in enumerate(orbs):
        orb.y += math.sin(time.time() * 2 + i) * 0.02
        orb.color = color.rgb(
            100 + math.sin(time.time() + i) * 50,
            150 + math.sin(time.time() * 1.5 + i) * 50,
            255
        )
    
    # Rotate mystery cubes
    for cube in mystery_cubes:
        cube.rotation_y += 30 * time.dt
        cube.rotation_x += 20 * time.dt
    
    # Camera shake for atmosphere
    if random.random() > 0.99:
        camera.shake(duration=0.3, magnitude=0.05)

# Tkinter overlay for stats
def create_tkinter_overlay():
    root = tk.Tk()
    root.title("B3313 Stats")
    root.geometry("200x150")
    root.attributes('-alpha', 0.8)
    root.attributes('-topmost', True)
    
    style = ttk.Style()
    style.configure('TLabel', background='black', foreground='lime')
    
    frame = tk.Frame(root, bg='black')
    frame.pack(fill='both', expand=True)
    
    fps_label = ttk.Label(frame, text="FPS: 60", style='TLabel')
    fps_label.pack(pady=5)
    
    pos_label = ttk.Label(frame, text="Position: 0, 0, 0", style='TLabel')
    pos_label.pack(pady=5)
    
    vibe_label = ttk.Label(frame, text="VIBE LEVEL: ████████", style='TLabel')
    vibe_label.pack(pady=5)
    
    def update_stats():
        while True:
            try:
                fps_label.config(text=f"FPS: {int(1/time.dt)}")
                pos_label.config(text=f"Pos: {int(player.x)}, {int(player.y)}, {int(player.z)}")
                vibe_level = "█" * int((math.sin(time.time() * 0.5) + 1) * 5)
                vibe_label.config(text=f"VIBE: {vibe_level}")
            except:
                pass
            time.sleep(0.1)
    
    stats_thread = threading.Thread(target=update_stats, daemon=True)
    stats_thread.start()
    
    root.mainloop()

# Start Tkinter in separate thread
tk_thread = threading.Thread(target=create_tkinter_overlay, daemon=True)
tk_thread.start()

# Instructions
Text('WASD: Move | Space: Double Jump | Mouse: Look Around', 
     position=(-0.8, -0.45), origin=(-1, -1), background=True)
Text('B3313 TECH DEMO - 60FPS', 
     position=(0, 0.48), origin=(0, 0), background=True, scale=2)

# Run the game
app.run()
