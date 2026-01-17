import pygame
import math
import random

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

# Colors
GREEN = (34, 139, 34)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

# Font for player names
FONT = pygame.font.Font(None, 20)
SCORE_FONT = pygame.font.Font(None, 36)
TIMER_FONT = pygame.font.Font(None, 48)

# Field dimensions
FIELD_MARGIN = 50
CENTER_LINE_WIDTH = 3

# Player settings
PLAYER_RADIUS = 15
PLAYER_SPEED = 4  # Reduced for slower game pace
PLAYER_COLOR = BLUE
RED_TEAM_COLOR = (200, 50, 50)
BLUE_TEAM_COLOR = (50, 50, 200)
MAX_STAMINA = 100
STAMINA_DRAIN_RATE = 0.4  # Reduced stamina drain for slower pace
STAMINA_REGEN_RATE = 0.15  # Stamina regained per frame when not running
STAMINA_SPEED_MULTIPLIER = 0.5  # Speed multiplier when stamina is low (below 30%)

# Ball settings
BALL_RADIUS = 10
BALL_COLOR = WHITE
BALL_FRICTION = 0.97  # Slightly more friction for slower ball movement
KICK_DISTANCE = 30  # Distance at which player can kick the ball
PASS_DISTANCE = 200  # Maximum distance for passing
PASS_SPEED = 10  # Reduced pass speed for slower game pace
DRIBBLE_DISTANCE = 25  # Maximum distance for dribbling
DRIBBLE_STRENGTH = 0.25  # Slightly reduced dribble strength for slower pace

# Goal post settings
GOAL_WIDTH = 100
GOAL_DEPTH = 20
GOAL_POST_WIDTH = 5

# AI and Difficulty settings
DIFFICULTY_LEVELS = {
    'easy': {'speed_multiplier': 0.8, 'decision_delay': 15, 'reaction_time': 5},
    'medium': {'speed_multiplier': 1.0, 'decision_delay': 8, 'reaction_time': 3},
    'hard': {'speed_multiplier': 1.2, 'decision_delay': 5, 'reaction_time': 1}
}
CURRENT_DIFFICULTY = 'medium'  # Can be changed to 'easy', 'medium', or 'hard'
AI_PASS_CHANCE = 0.3  # Probability of passing when near teammate (per frame)
AI_ATTACK_DISTANCE = 150  # Distance to consider attacking goal
AI_DEFEND_DISTANCE = 200  # Distance to consider defending
AI_CHASE_BALL_DISTANCE = 300  # Distance to chase free ball

# Match settings
MATCH_DURATION = 90  # Match duration in seconds
GOAL_COOLDOWN = 60  # Frames to wait after a goal before allowing another (prevents multiple goals)

# Penalty shootout settings
PENALTY_SPOT_X = WINDOW_WIDTH // 2
PENALTY_SPOT_Y_TOP = FIELD_MARGIN + 150  # For top goal (red team shoots)
PENALTY_SPOT_Y_BOTTOM = WINDOW_HEIGHT - FIELD_MARGIN - 150  # For bottom goal (blue team shoots)
PENALTY_KICK_POWER = 13  # Power of penalty kick (reduced for slower pace)
GOALKEEPER_SAVE_RANGE = 40  # Range goalkeeper can move to save
GOALKEEPER_REACTION_TIME = 20  # Frames before goalkeeper can react
GOALKEEPER_SAVE_CHANCE = 0.3  # Base chance of saving (30%)
PENALTY_SHOOTOUT_MAX_ROUNDS = 5  # Maximum rounds per team

class Player:
    def __init__(self, x, y, name, team='blue', position='midfielder', controllable=False,
                 speed_stat=5, stamina_stat=100, shooting_stat=8, dribbling_stat=0.3):
        self.x = x
        self.y = y
        self.radius = PLAYER_RADIUS
        self.team = team
        self.position = position
        self.controllable = controllable
        self.color = BLUE_TEAM_COLOR if team == 'blue' else RED_TEAM_COLOR
        self.name = name
        
        # Player stats
        self.speed_stat = speed_stat  # Base speed multiplier
        self.stamina_stat = stamina_stat  # Max stamina
        self.shooting_stat = shooting_stat  # Kick force multiplier
        self.dribbling_stat = dribbling_stat  # Dribble strength multiplier
        
        # Derived attributes based on stats
        self.base_speed = PLAYER_SPEED * (speed_stat / 5.0)  # Scale speed based on stat
        self.speed = self.base_speed
        self.stamina = stamina_stat
        self.max_stamina = stamina_stat
        self.is_moving = False
        
        # AI state
        self.ai_decision_timer = 0
        self.ai_target_x = x
        self.ai_target_y = y
        self.ai_state = 'idle'  # 'idle', 'chase_ball', 'attack', 'defend', 'support'
        
        # Penalty shootout state
        self.is_goalkeeper = (position == 'goalkeeper')
        self.penalty_save_position = 0  # Position for penalty saves (-1 to 1, left to right)
    
    def update_stamina(self):
        """Update stamina based on movement"""
        if self.is_moving:
            # Drain stamina when moving
            self.stamina = max(0, self.stamina - STAMINA_DRAIN_RATE)
        else:
            # Regenerate stamina when not moving
            self.stamina = min(self.max_stamina, self.stamina + STAMINA_REGEN_RATE)
        
        # Update speed based on stamina
        if self.stamina < 30:  # Low stamina threshold
            self.speed = self.base_speed * STAMINA_SPEED_MULTIPLIER
        else:
            self.speed = self.base_speed
    
    def move(self, dx, dy):
        # Track if player is moving
        self.is_moving = (dx != 0 or dy != 0)
        
        # Keep player within field bounds
        new_x = self.x + dx
        new_y = self.y + dy
        
        if FIELD_MARGIN <= new_x <= WINDOW_WIDTH - FIELD_MARGIN:
            self.x = new_x
        if FIELD_MARGIN <= new_y <= WINDOW_HEIGHT - FIELD_MARGIN:
            self.y = new_y
        
        # Update stamina after movement
        self.update_stamina()
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), self.radius, 2)
        
        # Draw player name above character
        name_surface = FONT.render(self.name, True, WHITE)
        name_rect = name_surface.get_rect(center=(int(self.x), int(self.y - self.radius - 15)))
        # Draw background for name for better visibility
        name_bg = pygame.Rect(name_rect.x - 2, name_rect.y - 1, name_rect.width + 4, name_rect.height + 2)
        pygame.draw.rect(screen, BLACK, name_bg)
        screen.blit(name_surface, name_rect)
        
        # Draw position indicator for controllable player
        if self.controllable:
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius + 3, 2)
            # Draw stamina bar above player (below name)
            bar_width = 40
            bar_height = 5
            bar_x = int(self.x - bar_width // 2)
            bar_y = int(self.y - self.radius - 10)
            
            # Background bar (red)
            pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
            # Stamina bar (green)
            stamina_width = int(bar_width * (self.stamina / self.max_stamina))
            if stamina_width > 0:
                pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, stamina_width, bar_height))
    
    def get_position(self):
        return (self.x, self.y)
    
    def distance_to(self, other_x, other_y):
        dx = self.x - other_x
        dy = self.y - other_y
        return math.sqrt(dx * dx + dy * dy)
    
    def separate_from_players(self, other_players, separation_distance=35):
        """Separate from other players to avoid overlapping"""
        separation_force_x = 0
        separation_force_y = 0
        separation_count = 0
        
        for other in other_players:
            if other == self:
                continue
            
            distance = self.distance_to(other.x, other.y)
            min_distance = self.radius + other.radius + 5  # Minimum distance between players
            
            if distance < min_distance and distance > 0:
                # Calculate separation direction (away from other player)
                dx = self.x - other.x
                dy = self.y - other.y
                # Normalize
                dx /= distance
                dy /= distance
                
                # Strength based on how close they are (closer = stronger push)
                strength = (min_distance - distance) / min_distance
                separation_force_x += dx * strength
                separation_force_y += dy * strength
                separation_count += 1
        
        # Apply separation force if needed
        if separation_count > 0:
            # Normalize the separation force
            separation_magnitude = math.sqrt(separation_force_x**2 + separation_force_y**2)
            if separation_magnitude > 0:
                separation_force_x /= separation_magnitude
                separation_force_y /= separation_magnitude
                
                # Apply separation movement (faster separation for stuck players)
                separation_speed = self.speed * 1.5
                new_x = self.x + separation_force_x * separation_speed
                new_y = self.y + separation_force_y * separation_speed
                
                # Keep within bounds
                if FIELD_MARGIN <= new_x <= WINDOW_WIDTH - FIELD_MARGIN:
                    self.x = new_x
                if FIELD_MARGIN <= new_y <= WINDOW_HEIGHT - FIELD_MARGIN:
                    self.y = new_y

class Ball:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.radius = BALL_RADIUS
        self.color = BALL_COLOR
    
    def update(self, players=None):
        # Apply friction
        self.vx *= BALL_FRICTION
        self.vy *= BALL_FRICTION
        
        # Stop if velocity is very small
        if abs(self.vx) < 0.1:
            self.vx = 0
        if abs(self.vy) < 0.1:
            self.vy = 0
        
        # Check for dribbling (ball close to player)
        if players:
            for player in players:
                distance = math.sqrt((self.x - player.x)**2 + (self.y - player.y)**2)
                if distance < DRIBBLE_DISTANCE + self.radius + player.radius:
                    # Apply dribbling force to keep ball close (based on player's dribbling stat)
                    dx = player.x - self.x
                    dy = player.y - self.y
                    dist = math.sqrt(dx*dx + dy*dy)
                    if dist > 0:
                        # Normalize and apply dribbling force
                        dx /= dist
                        dy /= dist
                        # Use player's dribbling stat to determine dribble strength
                        dribble_strength = DRIBBLE_STRENGTH * (player.dribbling_stat / 0.3)
                        self.vx += dx * dribble_strength
                        self.vy += dy * dribble_strength
                    break
        
        # Update position
        self.x += self.vx
        self.y += self.vy
        
        # Check if ball is in goal area before bouncing (to allow goals)
        center_x = WINDOW_WIDTH // 2
        goal_half_width = GOAL_WIDTH // 2
        in_goal_area = abs(self.x - center_x) < goal_half_width
        
        # Bounce off side boundaries
        if self.x - self.radius < FIELD_MARGIN:
            self.x = FIELD_MARGIN + self.radius
            self.vx = -self.vx * 0.7
        elif self.x + self.radius > WINDOW_WIDTH - FIELD_MARGIN:
            self.x = WINDOW_WIDTH - FIELD_MARGIN - self.radius
            self.vx = -self.vx * 0.7
        
        # Bounce off top/bottom boundaries only if not in goal area
        if not in_goal_area:
            if self.y - self.radius < FIELD_MARGIN:
                self.y = FIELD_MARGIN + self.radius
                self.vy = -self.vy * 0.7
            elif self.y + self.radius > WINDOW_HEIGHT - FIELD_MARGIN:
                self.y = WINDOW_HEIGHT - FIELD_MARGIN - self.radius
                self.vy = -self.vy * 0.7
    
    def kick(self, player_x, player_y, player_shooting_stat=8):
        # Calculate distance to player
        dx = self.x - player_x
        dy = self.y - player_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        # If player is close enough, kick the ball
        if distance < KICK_DISTANCE + self.radius + PLAYER_RADIUS:
            # Normalize direction
            if distance > 0:
                dx /= distance
                dy /= distance
            else:
                dx = 0
                dy = 1
            
            # Apply kick force based on player's shooting stat (reduced for slower pace)
            force = 6.5 * (player_shooting_stat / 8.0)
            self.vx += dx * force
            self.vy += dy * force
    
    def pass_to(self, target_x, target_y):
        # Direct pass to target position
        dx = target_x - self.x
        dy = target_y - self.y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance > 0:
            dx /= distance
            dy /= distance
            self.vx = dx * PASS_SPEED
            self.vy = dy * PASS_SPEED
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), self.radius, 2)
    
    def get_position(self):
        return (self.x, self.y)
    
    def check_goal(self):
        """Check if ball has entered a goal. Returns 'top', 'bottom', or None"""
        center_x = WINDOW_WIDTH // 2
        goal_half_width = GOAL_WIDTH // 2
        
        # Top goal (red team attacks here, blue team defends)
        if (abs(self.x - center_x) < goal_half_width and 
            self.y - self.radius < FIELD_MARGIN + GOAL_DEPTH):
            return 'top'
        
        # Bottom goal (blue team attacks here, red team defends)
        if (abs(self.x - center_x) < goal_half_width and 
            self.y + self.radius > WINDOW_HEIGHT - FIELD_MARGIN - GOAL_DEPTH):
            return 'bottom'
        
        return None

def draw_field(screen):
    # Draw green field
    field_rect = pygame.Rect(FIELD_MARGIN, FIELD_MARGIN, 
                            WINDOW_WIDTH - 2 * FIELD_MARGIN, 
                            WINDOW_HEIGHT - 2 * FIELD_MARGIN)
    pygame.draw.rect(screen, GREEN, field_rect)
    
    # Draw center line
    center_x = WINDOW_WIDTH // 2
    pygame.draw.line(screen, WHITE, 
                    (center_x, FIELD_MARGIN), 
                    (center_x, WINDOW_HEIGHT - FIELD_MARGIN), 
                    CENTER_LINE_WIDTH)
    
    # Draw center circle
    center_y = WINDOW_HEIGHT // 2
    pygame.draw.circle(screen, WHITE, (center_x, center_y), 60, 2)
    
    # Draw goal posts (top)
    top_goal_x = center_x
    top_goal_y = FIELD_MARGIN
    # Left post
    pygame.draw.rect(screen, WHITE, 
                    (top_goal_x - GOAL_WIDTH // 2, top_goal_y, 
                     GOAL_POST_WIDTH, GOAL_DEPTH))
    # Right post
    pygame.draw.rect(screen, WHITE, 
                    (top_goal_x + GOAL_WIDTH // 2 - GOAL_POST_WIDTH, top_goal_y, 
                     GOAL_POST_WIDTH, GOAL_DEPTH))
    # Crossbar
    pygame.draw.rect(screen, WHITE, 
                    (top_goal_x - GOAL_WIDTH // 2, top_goal_y, 
                     GOAL_WIDTH, GOAL_POST_WIDTH))
    
    # Draw goal posts (bottom)
    bottom_goal_x = center_x
    bottom_goal_y = WINDOW_HEIGHT - FIELD_MARGIN
    # Left post
    pygame.draw.rect(screen, WHITE, 
                    (bottom_goal_x - GOAL_WIDTH // 2, bottom_goal_y - GOAL_DEPTH, 
                     GOAL_POST_WIDTH, GOAL_DEPTH))
    # Right post
    pygame.draw.rect(screen, WHITE, 
                    (bottom_goal_x + GOAL_WIDTH // 2 - GOAL_POST_WIDTH, bottom_goal_y - GOAL_DEPTH, 
                     GOAL_POST_WIDTH, GOAL_DEPTH))
    # Crossbar
    pygame.draw.rect(screen, WHITE, 
                    (bottom_goal_x - GOAL_WIDTH // 2, bottom_goal_y - GOAL_POST_WIDTH, 
                     GOAL_WIDTH, GOAL_POST_WIDTH))

def draw_scoreboard(screen, blue_score, red_score, time_remaining, controllable_player=None):
    """Draw the scoreboard showing scores and match time"""
    # Draw background panel
    panel_rect = pygame.Rect(WINDOW_WIDTH // 2 - 150, 10, 300, 60)
    pygame.draw.rect(screen, (0, 0, 0, 200), panel_rect)
    pygame.draw.rect(screen, WHITE, panel_rect, 2)
    
    # Draw scores
    blue_text = SCORE_FONT.render(f"Blue: {blue_score}", True, BLUE_TEAM_COLOR)
    red_text = SCORE_FONT.render(f"Red: {red_score}", True, RED_TEAM_COLOR)
    
    screen.blit(blue_text, (WINDOW_WIDTH // 2 - 140, 20))
    screen.blit(red_text, (WINDOW_WIDTH // 2 + 20, 20))
    
    # Draw timer
    minutes = int(time_remaining // 60)
    seconds = int(time_remaining % 60)
    time_text = TIMER_FONT.render(f"{minutes:02d}:{seconds:02d}", True, WHITE)
    time_rect = time_text.get_rect(center=(WINDOW_WIDTH // 2, 50))
    screen.blit(time_text, time_rect)
    
    # Draw player switching instruction
    if controllable_player:
        switch_text = FONT.render(f"TAB: Switch Player | Current: {controllable_player.name}", True, WHITE)
        switch_rect = switch_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 20))
        # Draw background for better visibility
        switch_bg = pygame.Rect(switch_rect.x - 5, switch_rect.y - 2, switch_rect.width + 10, switch_rect.height + 4)
        pygame.draw.rect(screen, (0, 0, 0, 180), switch_bg)
        screen.blit(switch_text, switch_rect)

def draw_match_end(screen, blue_score, red_score, penalty_mode=False):
    """Draw match end screen with final score"""
    # Draw semi-transparent overlay
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    overlay.set_alpha(200)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    
    if not penalty_mode:
        # Draw match end text
        if blue_score > red_score:
            winner_text = SCORE_FONT.render("BLUE TEAM WINS!", True, BLUE_TEAM_COLOR)
        elif red_score > blue_score:
            winner_text = SCORE_FONT.render("RED TEAM WINS!", True, RED_TEAM_COLOR)
        else:
            winner_text = SCORE_FONT.render("DRAW!", True, WHITE)
        
        winner_rect = winner_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
        screen.blit(winner_text, winner_rect)
        
        # Draw final score
        final_score_text = SCORE_FONT.render(f"Final Score: Blue {blue_score} - {red_score} Red", True, WHITE)
        final_score_rect = final_score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        screen.blit(final_score_text, final_score_rect)
        
        # Draw instructions
        instruction_text = FONT.render("Press ESC to quit", True, WHITE)
        instruction_rect = instruction_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
        screen.blit(instruction_text, instruction_rect)

def draw_penalty_shootout(screen, blue_penalties, red_penalties, current_round, shooting_team, 
                          blue_score, red_score, penalty_result=None):
    """Draw penalty shootout UI"""
    # Draw background panel
    panel_rect = pygame.Rect(WINDOW_WIDTH // 2 - 200, WINDOW_HEIGHT // 2 - 100, 400, 200)
    pygame.draw.rect(screen, (0, 0, 0, 230), panel_rect)
    pygame.draw.rect(screen, WHITE, panel_rect, 3)
    
    # Draw title
    title_text = SCORE_FONT.render("PENALTY SHOOTOUT", True, WHITE)
    title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 80))
    screen.blit(title_text, title_rect)
    
    # Draw scores
    blue_pen_text = SCORE_FONT.render(f"Blue: {blue_penalties}/{current_round}", True, BLUE_TEAM_COLOR)
    red_pen_text = SCORE_FONT.render(f"Red: {red_penalties}/{current_round}", True, RED_TEAM_COLOR)
    screen.blit(blue_pen_text, (WINDOW_WIDTH // 2 - 180, WINDOW_HEIGHT // 2 - 40))
    screen.blit(red_pen_text, (WINDOW_WIDTH // 2 + 60, WINDOW_HEIGHT // 2 - 40))
    
    # Draw current shooter
    if shooting_team:
        shooter_text = FONT.render(f"{shooting_team.upper()} TEAM SHOOTING", True, WHITE)
        shooter_rect = shooter_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        screen.blit(shooter_text, shooter_rect)
    
    # Draw result
    if penalty_result:
        if penalty_result == 'goal':
            result_text = SCORE_FONT.render("GOAL!", True, (0, 255, 0))
        else:
            result_text = SCORE_FONT.render("SAVED!", True, RED)
        result_rect = result_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 30))
        screen.blit(result_text, result_rect)
    
    # Draw instructions
    if not penalty_result:
        if shooting_team == 'blue':
            inst_text = FONT.render("Press SPACE to shoot (UP/DOWN to aim)", True, WHITE)
        else:
            inst_text = FONT.render("AI is shooting...", True, WHITE)
        inst_rect = inst_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 60))
        screen.blit(inst_text, inst_rect)

def create_team(team_name, start_y, field_width, field_height):
    """Create a team of 5 players with positions, names, and stats"""
    players = []
    center_x = field_width // 2
    field_start_x = FIELD_MARGIN
    field_end_x = field_width - FIELD_MARGIN
    
    # Real players with stats based on positions
    # Format: (name, position, x_offset, y_offset, speed, stamina, shooting, dribbling)
    if team_name == 'blue':
        player_data = [
            ('Neuer', 'goalkeeper', 0, 0, 3, 80, 4, 0.2),  # Goalkeeper - slower, less shooting
            ('Ramos', 'defender', -80, 60, 4, 90, 6, 0.25),  # Defender - balanced
            ('Modric', 'midfielder', -40, 100, 6, 95, 7, 0.4),  # Midfielder - good dribbling, speed
            ('De Bruyne', 'midfielder', 40, 100, 5, 100, 9, 0.35),  # Midfielder - great shooting
            ('Messi', 'forward', 0, 140, 7, 85, 10, 0.5)  # Forward - best shooting and dribbling
        ]
    else:  # red team
        player_data = [
            ('Courtois', 'goalkeeper', 0, 0, 3, 80, 4, 0.2),  # Goalkeeper
            ('Van Dijk', 'defender', -80, 60, 4, 90, 6, 0.25),  # Defender
            ('Kroos', 'midfielder', -40, 100, 5, 100, 8, 0.3),  # Midfielder
            ('Pogba', 'midfielder', 40, 100, 6, 95, 7, 0.4),  # Midfielder
            ('Ronaldo', 'forward', 0, 140, 6, 90, 10, 0.35)  # Forward - great shooting
        ]
    
    # Position setup: goalkeeper, defender, midfielder, midfielder, forward
    for i, (name, pos, x_offset, y_offset, speed, stamina, shooting, dribbling) in enumerate(player_data):
        x = center_x + x_offset
        y = start_y + y_offset
        
        # All blue team players can be controlled (switching enabled)
        # First midfielder starts as controllable
        controllable = (team_name == 'blue' and i == 2)
        player = Player(x, y, name, team=team_name, position=pos, controllable=controllable,
                       speed_stat=speed, stamina_stat=stamina, shooting_stat=shooting, dribbling_stat=dribbling)
        players.append(player)
    
    return players

def find_nearest_teammate(player, teammates, ball):
    """Find the nearest teammate to pass to"""
    nearest = None
    min_distance = PASS_DISTANCE
    
    for teammate in teammates:
        if teammate == player:
            continue
        
        # Check if teammate is in front of player (towards opponent goal)
        if player.team == 'blue':
            # Blue team attacks downward
            if teammate.y > player.y:
                distance = player.distance_to(teammate.x, teammate.y)
                if distance < min_distance:
                    min_distance = distance
                    nearest = teammate
        else:
            # Red team attacks upward
            if teammate.y < player.y:
                distance = player.distance_to(teammate.x, teammate.y)
                if distance < min_distance:
                    min_distance = distance
                    nearest = teammate
    
    return nearest

def find_nearest_opponent(player, opponents):
    """Find the nearest opponent player"""
    nearest = None
    min_distance = float('inf')
    
    for opponent in opponents:
        distance = player.distance_to(opponent.x, opponent.y)
        if distance < min_distance:
            min_distance = distance
            nearest = opponent
    
    return nearest

def get_goal_position(team):
    """Get the target goal position for a team"""
    center_x = WINDOW_WIDTH // 2
    if team == 'blue':
        # Blue team attacks downward (bottom goal)
        return (center_x, WINDOW_HEIGHT - FIELD_MARGIN - GOAL_DEPTH)
    else:
        # Red team attacks upward (top goal)
        return (center_x, FIELD_MARGIN + GOAL_DEPTH)

def get_home_position(player, team_players):
    """Get the player's home/base position based on their role"""
    center_x = WINDOW_WIDTH // 2
    field_center_y = WINDOW_HEIGHT // 2
    
    # Find player index in team
    player_index = -1
    for i, p in enumerate(team_players):
        if p == player:
            player_index = i
            break
    
    if player_index == -1:
        return (player.x, player.y)
    
    # Position based on role and team
    if player.team == 'blue':
        # Blue team starts at top
        start_y = FIELD_MARGIN + 50
        positions = [
            (center_x, start_y),  # Goalkeeper
            (center_x - 80, start_y + 60),  # Defender
            (center_x - 40, start_y + 100),  # Midfielder 1
            (center_x + 40, start_y + 100),  # Midfielder 2
            (center_x, start_y + 140)  # Forward
        ]
    else:
        # Red team starts at bottom
        start_y = WINDOW_HEIGHT - FIELD_MARGIN - 200
        positions = [
            (center_x, start_y),  # Goalkeeper
            (center_x - 80, start_y + 60),  # Defender
            (center_x - 40, start_y + 100),  # Midfielder 1
            (center_x + 40, start_y + 100),  # Midfielder 2
            (center_x, start_y + 140)  # Forward
        ]
    
    if 0 <= player_index < len(positions):
        return positions[player_index]
    return (player.x, player.y)

def update_goalkeeper_penalty(goalkeeper, ball, shooting_team, difficulty='medium'):
    """Update goalkeeper position during penalty kick - fast and realistic"""
    if not goalkeeper.is_goalkeeper:
        return
    
    diff_settings = DIFFICULTY_LEVELS.get(difficulty, DIFFICULTY_LEVELS['medium'])
    reaction_time = max(1, diff_settings['reaction_time'] // 2)  # Faster reaction for goalkeepers
    
    # Determine goal position
    if shooting_team == 'blue':
        # Blue shoots at bottom goal, goalkeeper at top
        goal_center_x = WINDOW_WIDTH // 2
        goal_center_y = FIELD_MARGIN + GOAL_DEPTH // 2
        goal_range = GOAL_WIDTH // 2
    else:
        # Red shoots at top goal, goalkeeper at bottom
        goal_center_x = WINDOW_WIDTH // 2
        goal_center_y = WINDOW_HEIGHT - FIELD_MARGIN - GOAL_DEPTH // 2
        goal_range = GOAL_WIDTH // 2
    
    # If ball is moving, try to predict where it will go and move towards it immediately
    if abs(ball.vx) > 0.3 or abs(ball.vy) > 0.3:
        # Ball is moving - predict and react quickly
        # Predict ball's x position when it reaches goal line
        if shooting_team == 'blue':
            # Ball moving towards top goal
            time_to_goal = abs((goal_center_y - ball.y) / ball.vy) if abs(ball.vy) > 0.1 else 10
        else:
            # Ball moving towards bottom goal
            time_to_goal = abs((goal_center_y - ball.y) / ball.vy) if abs(ball.vy) > 0.1 else 10
        
        # More accurate prediction with multiple steps
        predicted_x = ball.x + (ball.vx * time_to_goal)
        # Add slight adjustment based on ball acceleration (friction)
        predicted_x += ball.vx * 0.5  # Account for ball slowing down
        
        # Clamp predicted position to goal width
        predicted_x = max(goal_center_x - goal_range, min(goal_center_x + goal_range, predicted_x))
        target_x = predicted_x
        
        # Update saved position for save chance calculation
        goal_x_offset = predicted_x - goal_center_x
        goalkeeper.penalty_save_position = goal_x_offset / goal_range if goal_range > 0 else 0
    else:
        # Ball not moving much, use saved position or center
        if abs(goalkeeper.penalty_save_position) > 0.1:
            target_x = goal_center_x + (goalkeeper.penalty_save_position * goal_range * 0.8)
        else:
            target_x = goal_center_x
    
    target_y = goal_center_y
    
    # Fast, direct movement towards target
    dx = target_x - goalkeeper.x
    dy = target_y - goalkeeper.y
    distance = math.sqrt(dx*dx + dy*dy)
    
    if distance > 1:  # Smaller threshold for more responsive movement
        if distance > 0:
            dx /= distance
            dy /= distance
        
        # Goalkeeper moves much faster during penalty (2x speed boost)
        # Higher difficulty = faster goalkeeper
        speed_multiplier = diff_settings.get('speed_multiplier', 1.0)
        goalkeeper.move(dx * goalkeeper.speed * 2.5 * speed_multiplier, dy * goalkeeper.speed * 2.5 * speed_multiplier)
    else:
        goalkeeper.is_moving = False

def check_penalty_save(goalkeeper, ball, shooting_team):
    """Check if goalkeeper saves the penalty"""
    if not goalkeeper.is_goalkeeper:
        return False
    
    # Determine goal position
    if shooting_team == 'blue':
        goal_center_y = FIELD_MARGIN + GOAL_DEPTH // 2
    else:
        goal_center_y = WINDOW_HEIGHT - FIELD_MARGIN - GOAL_DEPTH // 2
    
    goal_center_x = WINDOW_WIDTH // 2
    
    # Check if ball is in goal area (with some tolerance)
    if abs(ball.y - goal_center_y) > GOAL_DEPTH + 10:
        return False
    
    if abs(ball.x - goal_center_x) > GOAL_WIDTH // 2 + 5:
        return False
    
    # Check if goalkeeper is close enough to ball
    distance = math.sqrt((goalkeeper.x - ball.x)**2 + (goalkeeper.y - ball.y)**2)
    
    # Save chance based on distance and base save chance
    save_chance = GOALKEEPER_SAVE_CHANCE
    if distance < GOALKEEPER_SAVE_RANGE:
        # Closer = better chance (up to 80% if very close)
        save_chance += (1 - distance / GOALKEEPER_SAVE_RANGE) * 0.5
    
    # Check if goalkeeper position matches ball position
    goal_x_offset = ball.x - goal_center_x
    goal_x_normalized = goal_x_offset / (GOAL_WIDTH // 2) if GOAL_WIDTH > 0 else 0  # -1 to 1
    position_match = abs(goalkeeper.penalty_save_position - goal_x_normalized) < 0.4
    
    if position_match:
        save_chance += 0.25  # Bonus if goalkeeper is in right position
    
    # Cap save chance
    save_chance = min(0.85, save_chance)  # Max 85% save chance
    
    return random.random() < save_chance

def execute_penalty_kick(ball, shooting_team, aim_direction=0):
    """Execute a penalty kick. aim_direction: -1 (left) to 1 (right), 0 is center"""
    if shooting_team == 'blue':
        # Blue shoots at bottom goal
        ball.x = PENALTY_SPOT_X
        ball.y = PENALTY_SPOT_Y_BOTTOM
        goal_x = WINDOW_WIDTH // 2
        goal_y = WINDOW_HEIGHT - FIELD_MARGIN - GOAL_DEPTH // 2
    else:
        # Red shoots at top goal
        ball.x = PENALTY_SPOT_X
        ball.y = PENALTY_SPOT_Y_TOP
        goal_x = WINDOW_WIDTH // 2
        goal_y = FIELD_MARGIN + GOAL_DEPTH // 2
    
    # Calculate direction to goal with aim offset
    goal_width_half = GOAL_WIDTH // 2
    target_x = goal_x + (aim_direction * goal_width_half * 0.7)  # 70% of goal width for aim
    
    dx = target_x - ball.x
    dy = goal_y - ball.y
    distance = math.sqrt(dx*dx + dy*dy)
    
    if distance > 0:
        dx /= distance
        dy /= distance
    
    # Apply kick force
    ball.vx = dx * PENALTY_KICK_POWER
    ball.vy = dy * PENALTY_KICK_POWER

def update_ai_player(player, ball, teammates, opponents, difficulty='medium'):
    """Update AI-controlled player behavior - fast and realistic"""
    if player.controllable:
        return  # Skip AI for controllable player
    
    # Get difficulty settings
    diff_settings = DIFFICULTY_LEVELS.get(difficulty, DIFFICULTY_LEVELS['medium'])
    speed_mult = diff_settings['speed_multiplier']
    decision_delay = diff_settings['decision_delay']
    reaction_time = diff_settings['reaction_time']
    
    # Update decision timer
    player.ai_decision_timer += 1
    
    # Calculate distances
    ball_distance = player.distance_to(ball.x, ball.y)
    goal_x, goal_y = get_goal_position(player.team)
    goal_distance = player.distance_to(goal_x, goal_y)
    
    # Check if player has ball (close enough to dribble)
    has_ball = ball_distance < DRIBBLE_DISTANCE + ball.radius + player.radius
    
    # For critical actions (ball nearby), update target immediately for faster reaction
    urgent_update = ball_distance < AI_CHASE_BALL_DISTANCE
    very_urgent = ball_distance < 80  # Very close - react immediately
    
    # Decision making (update more frequently for urgent situations)
    # Very urgent situations bypass all delays
    should_update_decision = (player.ai_decision_timer >= decision_delay) or (urgent_update and player.ai_decision_timer >= max(1, reaction_time)) or very_urgent
    
    if should_update_decision:
        # Reset timer if we're doing a full decision update
        if player.ai_decision_timer >= decision_delay:
            player.ai_decision_timer = 0
        
        # Determine AI state
        if has_ball:
            # Player has the ball - decide: attack, pass, or dribble
            nearest_teammate = find_nearest_teammate(player, teammates, ball)
            
            # Check if should pass (if teammate is in good position)
            if nearest_teammate and player.distance_to(nearest_teammate.x, nearest_teammate.y) < PASS_DISTANCE:
                # Check if teammate is closer to goal
                teammate_goal_dist = nearest_teammate.distance_to(goal_x, goal_y)
                if teammate_goal_dist < goal_distance - 30:  # Teammate is significantly closer
                    # Pass to teammate
                    ball.pass_to(nearest_teammate.x, nearest_teammate.y)
                    player.ai_state = 'support'
                    return
            
            # Attack goal if close enough
            if goal_distance < AI_ATTACK_DISTANCE:
                player.ai_state = 'attack'
                # Predict ball movement for better targeting
                player.ai_target_x = goal_x
                player.ai_target_y = goal_y
            else:
                # Dribble towards goal
                player.ai_state = 'attack'
                # Move towards goal with predictive positioning
                dx_to_goal = goal_x - player.x
                dy_to_goal = goal_y - player.y
                dist_to_goal = math.sqrt(dx_to_goal**2 + dy_to_goal**2)
                if dist_to_goal > 0:
                    # More aggressive forward movement
                    player.ai_target_x = player.x + (dx_to_goal / dist_to_goal) * 60
                    player.ai_target_y = player.y + (dy_to_goal / dist_to_goal) * 60
        else:
            # Player doesn't have ball
            nearest_opponent = find_nearest_opponent(player, opponents)
            ball_carrier = None
            
            # Find who has the ball (with prediction for moving ball)
            for p in teammates + opponents:
                if p.distance_to(ball.x, ball.y) < DRIBBLE_DISTANCE + ball.radius + p.radius:
                    ball_carrier = p
                    break
            
            if ball_carrier and ball_carrier.team == player.team:
                # Teammate has ball - support/position for pass
                player.ai_state = 'support'
                # Position ahead of ball carrier with better spacing
                if player.team == 'blue':
                    player.ai_target_x = ball.x + (ball.vx * 10)  # Predict ball position
                    player.ai_target_y = ball.y + (ball.vy * 10) + 80
                else:
                    player.ai_target_x = ball.x + (ball.vx * 10)
                    player.ai_target_y = ball.y + (ball.vy * 10) - 80
            elif ball_carrier and ball_carrier.team != player.team:
                # Opponent has ball - defend aggressively
                if ball_distance < AI_DEFEND_DISTANCE:
                    player.ai_state = 'defend'
                    # Intercept ball with prediction
                    player.ai_target_x = ball.x + (ball.vx * 5)
                    player.ai_target_y = ball.y + (ball.vy * 5)
                else:
                    # Return to home position
                    home_x, home_y = get_home_position(player, teammates)
                    player.ai_state = 'defend'
                    player.ai_target_x = home_x
                    player.ai_target_y = home_y
            else:
                # Ball is free - chase it aggressively
                if ball_distance < AI_CHASE_BALL_DISTANCE:
                    player.ai_state = 'chase_ball'
                    # Predict ball position for better interception
                    player.ai_target_x = ball.x + (ball.vx * 8)
                    player.ai_target_y = ball.y + (ball.vy * 8)
                else:
                    # Return to home position
                    home_x, home_y = get_home_position(player, teammates)
                    player.ai_state = 'idle'
                    player.ai_target_x = home_x
                    player.ai_target_y = home_y
    
    # Move towards target (immediate movement, no reaction delay for urgent situations)
    can_move = (player.ai_decision_timer >= reaction_time) or urgent_update or very_urgent
    
    if can_move:
        dx = player.ai_target_x - player.x
        dy = player.ai_target_y - player.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance > 3:  # Only move if not already at target (smaller threshold for smoother movement)
            # Normalize direction
            if distance > 0:
                dx /= distance
                dy /= distance
            
            # Apply speed with difficulty multiplier (boost for urgent situations)
            urgency_boost = 1.25 if very_urgent else (1.15 if urgent_update else 1.0)
            move_speed = player.speed * speed_mult * urgency_boost
            player.move(dx * move_speed, dy * move_speed)
            
            # Kick ball if close and not dribbling
            if not has_ball and ball_distance < KICK_DISTANCE + ball.radius + player.radius:
                ball.kick(player.x, player.y, player.shooting_stat)
        else:
            player.is_moving = False

def main():
    # Set up the display
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Football Game - Difficulty: " + CURRENT_DIFFICULTY.title())
    clock = pygame.time.Clock()
    
    # Create two teams
    blue_team = create_team('blue', FIELD_MARGIN + 50, WINDOW_WIDTH, WINDOW_HEIGHT)
    red_team = create_team('red', WINDOW_HEIGHT - FIELD_MARGIN - 200, WINDOW_WIDTH, WINDOW_HEIGHT)
    
    all_players = blue_team + red_team
    controllable_player_index = 0  # Index of currently controllable player in blue_team
    controllable_player = blue_team[controllable_player_index] if blue_team else None
    # Set initial controllable player
    for i, player in enumerate(blue_team):
        player.controllable = (i == controllable_player_index)
    
    # Create ball at center
    ball = Ball(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
    
    # Match state
    blue_score = 0
    red_score = 0
    match_time = MATCH_DURATION  # Match duration in seconds
    match_ended = False
    goal_cooldown = 0  # Prevent multiple goals from same event
    
    # Game loop
    running = True
    space_just_pressed = False
    current_difficulty = CURRENT_DIFFICULTY
    last_time = pygame.time.get_ticks()  # For timer
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not match_ended:
                    space_just_pressed = True
                # Player switching with TAB key
                elif event.key == pygame.K_TAB and not match_ended:
                    # Cycle through blue team players
                    controllable_player.controllable = False
                    controllable_player_index = (controllable_player_index + 1) % len(blue_team)
                    controllable_player = blue_team[controllable_player_index]
                    controllable_player.controllable = True
                # Change difficulty with number keys (only before match ends)
                elif event.key == pygame.K_1 and not match_ended:
                    current_difficulty = 'easy'
                    pygame.display.set_caption("Football Game - Difficulty: Easy")
                elif event.key == pygame.K_2 and not match_ended:
                    current_difficulty = 'medium'
                    pygame.display.set_caption("Football Game - Difficulty: Medium")
                elif event.key == pygame.K_3 and not match_ended:
                    current_difficulty = 'hard'
                    pygame.display.set_caption("Football Game - Difficulty: Hard")
                elif event.key == pygame.K_ESCAPE:
                    running = False
        
        # Update match timer (only if match hasn't ended)
        if not match_ended:
            current_time = pygame.time.get_ticks()
            elapsed = (current_time - last_time) / 1000.0  # Convert to seconds
            match_time -= elapsed
            last_time = current_time
            
            # Check if match time is up
            if match_time <= 0:
                match_time = 0
                match_ended = True
        
        # Decrease goal cooldown
        if goal_cooldown > 0:
            goal_cooldown -= 1
        
        # Handle keyboard input for controllable player (only if match hasn't ended)
        keys = pygame.key.get_pressed()
        dx = 0
        dy = 0
        
        if controllable_player and not match_ended:
            if keys[pygame.K_LEFT]:
                dx -= controllable_player.speed
            if keys[pygame.K_RIGHT]:
                dx += controllable_player.speed
            if keys[pygame.K_UP]:
                dy -= controllable_player.speed
            if keys[pygame.K_DOWN]:
                dy += controllable_player.speed
            
            # Move controllable player
            if dx != 0 or dy != 0:
                controllable_player.move(dx, dy)
                # Check if player is close to ball and kick it (only if not dribbling)
                ball_distance = controllable_player.distance_to(ball.x, ball.y)
                if ball_distance > DRIBBLE_DISTANCE + ball.radius + controllable_player.radius:
                    ball.kick(controllable_player.x, controllable_player.y, controllable_player.shooting_stat)
            else:
                # Player not moving, mark for stamina regeneration
                controllable_player.is_moving = False
            
            # Handle passing (SPACE key)
            if space_just_pressed:
                # Check if player has the ball
                ball_distance = controllable_player.distance_to(ball.x, ball.y)
                if ball_distance < KICK_DISTANCE + ball.radius + controllable_player.radius:
                    # Find nearest teammate
                    teammates = blue_team if controllable_player.team == 'blue' else red_team
                    nearest_teammate = find_nearest_teammate(controllable_player, teammates, ball)
                    if nearest_teammate:
                        ball.pass_to(nearest_teammate.x, nearest_teammate.y)
                space_just_pressed = False
        
        # Update AI for CPU-controlled players (only if match hasn't ended)
        if not match_ended:
            # Update AI for CPU-controlled players (red team and blue team non-controllable)
            for player in red_team:
                if not player.controllable:
                    update_ai_player(player, ball, red_team, blue_team, current_difficulty)
            
            # Update AI for blue team non-controllable players
            for player in blue_team:
                if not player.controllable:
                    update_ai_player(player, ball, blue_team, red_team, current_difficulty)
        
        # Apply collision avoidance/separation for all players
        if not match_ended:
            for player in all_players:
                player.separate_from_players(all_players)
        
        # Update stamina for all players (regeneration when not moving)
        for player in all_players:
            if not player.is_moving:
                player.update_stamina()
        
        # Update ball physics with dribbling support
        if not match_ended:
            ball.update(all_players)
            
            # Check for goals
            if goal_cooldown == 0:
                goal_result = ball.check_goal()
                if goal_result == 'top':
                    # Blue team scores (ball entered top goal)
                    blue_score += 1
                    goal_cooldown = GOAL_COOLDOWN
                    # Reset ball to center
                    ball = Ball(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
                    # Reset player positions
                    blue_team = create_team('blue', FIELD_MARGIN + 50, WINDOW_WIDTH, WINDOW_HEIGHT)
                    red_team = create_team('red', WINDOW_HEIGHT - FIELD_MARGIN - 200, WINDOW_WIDTH, WINDOW_HEIGHT)
                    all_players = blue_team + red_team
                    # Restore controllable player
                    controllable_player_index = min(controllable_player_index, len(blue_team) - 1)
                    controllable_player = blue_team[controllable_player_index]
                    for i, player in enumerate(blue_team):
                        player.controllable = (i == controllable_player_index)
                elif goal_result == 'bottom':
                    # Red team scores (ball entered bottom goal)
                    red_score += 1
                    goal_cooldown = GOAL_COOLDOWN
                    # Reset ball to center
                    ball = Ball(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
                    # Reset player positions
                    blue_team = create_team('blue', FIELD_MARGIN + 50, WINDOW_WIDTH, WINDOW_HEIGHT)
                    red_team = create_team('red', WINDOW_HEIGHT - FIELD_MARGIN - 200, WINDOW_WIDTH, WINDOW_HEIGHT)
                    all_players = blue_team + red_team
                    # Restore controllable player
                    controllable_player_index = min(controllable_player_index, len(blue_team) - 1)
                    controllable_player = blue_team[controllable_player_index]
                    for i, player in enumerate(blue_team):
                        player.controllable = (i == controllable_player_index)
        
        # Draw everything
        screen.fill(BLACK)
        draw_field(screen)
        
        # Draw all players
        for player in all_players:
            player.draw(screen)
        
        # Draw ball
        ball.draw(screen)
        
        # Draw scoreboard
        draw_scoreboard(screen, blue_score, red_score, max(0, match_time), controllable_player)
        
        # Draw match end screen if match has ended (but not penalty shootout)
        if match_ended and blue_score != red_score:
            draw_match_end(screen, blue_score, red_score)
        
        pygame.display.flip()
        clock.tick(FPS)
    
    # Start penalty shootout if match ended in draw
    if match_ended and blue_score == red_score:
        # Penalty shootout mode
        penalty_shootout(screen, clock, blue_team, red_team, blue_score, red_score, current_difficulty)
    
    pygame.quit()

def penalty_shootout(screen, clock, blue_team, red_team, blue_score, red_score, difficulty):
    """Penalty shootout mode when match ends in draw"""
    # Penalty shootout state
    blue_penalties = 0
    red_penalties = 0
    current_round = 0
    shooting_team = 'blue'  # Blue shoots first
    penalty_phase = 'setup'  # 'setup', 'shooting', 'result'
    penalty_result = None
    penalty_result_timer = 0
    penalty_aim = 0  # -1 to 1, for player aiming
    ball = Ball(PENALTY_SPOT_X, PENALTY_SPOT_Y_BOTTOM)
    
    # Get goalkeepers
    blue_goalkeeper = None
    red_goalkeeper = None
    for player in blue_team:
        if player.is_goalkeeper:
            blue_goalkeeper = player
            break
    for player in red_team:
        if player.is_goalkeeper:
            red_goalkeeper = player
            break
    
    running = True
    space_just_pressed = False
    
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and penalty_phase == 'setup' and shooting_team == 'blue':
                    space_just_pressed = True
                elif event.key == pygame.K_ESCAPE:
                    running = False
        
        # Handle aiming for player (blue team)
        keys = pygame.key.get_pressed()
        if penalty_phase == 'setup' and shooting_team == 'blue':
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                penalty_aim = max(-1, penalty_aim - 0.05)
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                penalty_aim = min(1, penalty_aim + 0.05)
        
        # Update penalty shootout logic
        if penalty_phase == 'setup':
            # Position ball and goalkeeper
            if shooting_team == 'blue':
                ball.x = PENALTY_SPOT_X
                ball.y = PENALTY_SPOT_Y_BOTTOM
                ball.vx = 0
                ball.vy = 0
                # Position red goalkeeper
                if red_goalkeeper:
                    goal_center_x = WINDOW_WIDTH // 2
                    goal_center_y = WINDOW_HEIGHT - FIELD_MARGIN - GOAL_DEPTH // 2
                    red_goalkeeper.x = goal_center_x
                    red_goalkeeper.y = goal_center_y
                    # Goalkeeper randomly chooses position (with some AI)
                    if random.random() < 0.3:  # 30% chance to move
                        red_goalkeeper.penalty_save_position = random.uniform(-0.8, 0.8)
            else:
                ball.x = PENALTY_SPOT_X
                ball.y = PENALTY_SPOT_Y_TOP
                ball.vx = 0
                ball.vy = 0
                # Position blue goalkeeper
                if blue_goalkeeper:
                    goal_center_x = WINDOW_WIDTH // 2
                    goal_center_y = FIELD_MARGIN + GOAL_DEPTH // 2
                    blue_goalkeeper.x = goal_center_x
                    blue_goalkeeper.y = goal_center_y
                    # Goalkeeper randomly chooses position
                    if random.random() < 0.3:
                        blue_goalkeeper.penalty_save_position = random.uniform(-0.8, 0.8)
            
            # Execute penalty kick
            if shooting_team == 'blue' and space_just_pressed:
                execute_penalty_kick(ball, 'blue', penalty_aim)
                penalty_phase = 'shooting'
                space_just_pressed = False
            elif shooting_team == 'red':
                # AI shoots after a delay
                if random.random() < 0.02:  # 2% chance per frame (about 1 second delay)
                    ai_aim = random.uniform(-0.7, 0.7)  # AI aims randomly
                    execute_penalty_kick(ball, 'red', ai_aim)
                    penalty_phase = 'shooting'
        
        elif penalty_phase == 'shooting':
            # Update ball physics
            ball.update()
            
            # Update goalkeeper during penalty
            if shooting_team == 'blue' and red_goalkeeper:
                update_goalkeeper_penalty(red_goalkeeper, ball, 'blue', difficulty)
            elif shooting_team == 'red' and blue_goalkeeper:
                update_goalkeeper_penalty(blue_goalkeeper, ball, 'red', difficulty)
            
            # Check if ball entered goal or went out
            goal_result = ball.check_goal()
            ball_stopped = abs(ball.vx) < 0.1 and abs(ball.vy) < 0.1
            ball_out = (ball.x < FIELD_MARGIN or ball.x > WINDOW_WIDTH - FIELD_MARGIN or
                       ball.y < FIELD_MARGIN or ball.y > WINDOW_HEIGHT - FIELD_MARGIN)
            
            if goal_result:
                # Check if goalkeeper saved it (check immediately when ball enters goal area)
                saved = False
                if shooting_team == 'blue' and red_goalkeeper:
                    saved = check_penalty_save(red_goalkeeper, ball, 'blue')
                elif shooting_team == 'red' and blue_goalkeeper:
                    saved = check_penalty_save(blue_goalkeeper, ball, 'red')
                
                if saved:
                    penalty_result = 'saved'
                else:
                    penalty_result = 'goal'
                    if shooting_team == 'blue':
                        blue_penalties += 1
                    else:
                        red_penalties += 1
                penalty_phase = 'result'
                penalty_result_timer = 0
            elif ball_stopped or ball_out:
                # Ball missed or stopped
                penalty_result = 'missed'
                penalty_phase = 'result'
                penalty_result_timer = 0
        
        elif penalty_phase == 'result':
            penalty_result_timer += 1
            
            # Wait 2 seconds before next penalty
            if penalty_result_timer > 120:  # 2 seconds at 60 FPS
                # Switch teams
                if shooting_team == 'blue':
                    shooting_team = 'red'
                else:
                    shooting_team = 'blue'
                    current_round += 1
                
                # Check if shootout is over
                # After initial rounds, continue until there's a clear winner
                if current_round >= PENALTY_SHOOTOUT_MAX_ROUNDS:
                    # After max rounds, it's sudden death
                    # Check if one team is ahead after a complete round (both teams have shot)
                    if shooting_team == 'red':  # Red just shot, so we've completed a full round
                        if blue_penalties != red_penalties:
                            # One team is ahead, end shootout
                            running = False
                        # If tied, continue (sudden death continues)
                
                penalty_phase = 'setup'
                penalty_result = None
                penalty_aim = 0
        
        # Draw everything
        screen.fill(BLACK)
        draw_field(screen)
        
        # Draw players (only goalkeepers during penalty)
        if shooting_team == 'blue' and red_goalkeeper:
            red_goalkeeper.draw(screen)
        elif shooting_team == 'red' and blue_goalkeeper:
            blue_goalkeeper.draw(screen)
        
        # Draw ball
        ball.draw(screen)
        
        # Draw penalty shootout UI
        draw_penalty_shootout(screen, blue_penalties, red_penalties, current_round, 
                            shooting_team if penalty_phase == 'setup' else None,
                            blue_score, red_score, penalty_result)
        
        # Draw aim indicator for player
        if penalty_phase == 'setup' and shooting_team == 'blue':
            aim_x = WINDOW_WIDTH // 2 + (penalty_aim * GOAL_WIDTH // 2 * 0.7)
            aim_y = WINDOW_HEIGHT - FIELD_MARGIN - GOAL_DEPTH // 2
            pygame.draw.circle(screen, (255, 255, 0), (int(aim_x), int(aim_y)), 5)
        
        pygame.display.flip()
        clock.tick(FPS)
    
    # Show final penalty shootout result
    final_blue_score = blue_score + blue_penalties
    final_red_score = red_score + red_penalties
    
    # Display final result screen
    showing_result = True
    result_timer = 0
    while showing_result:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                showing_result = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_SPACE:
                    showing_result = False
        
        screen.fill(BLACK)
        draw_field(screen)
        
        # Draw final result
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        if blue_penalties > red_penalties:
            winner_text = SCORE_FONT.render("BLUE TEAM WINS!", True, BLUE_TEAM_COLOR)
        elif red_penalties > blue_penalties:
            winner_text = SCORE_FONT.render("RED TEAM WINS!", True, RED_TEAM_COLOR)
        else:
            winner_text = SCORE_FONT.render("DRAW!", True, WHITE)
        
        winner_rect = winner_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 80))
        screen.blit(winner_text, winner_rect)
        
        # Draw scores
        match_score_text = SCORE_FONT.render(f"Match: Blue {blue_score} - {red_score} Red", True, WHITE)
        match_score_rect = match_score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 30))
        screen.blit(match_score_text, match_score_rect)
        
        penalty_score_text = SCORE_FONT.render(f"Penalties: Blue {blue_penalties} - {red_penalties} Red", True, WHITE)
        penalty_score_rect = penalty_score_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20))
        screen.blit(penalty_score_text, penalty_score_rect)
        
        instruction_text = FONT.render("Press ESC or SPACE to quit", True, WHITE)
        instruction_rect = instruction_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 70))
        screen.blit(instruction_text, instruction_rect)
        
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()

