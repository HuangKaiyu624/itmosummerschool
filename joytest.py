import pygame
import socket
import struct
import math
import time
# 初始化pygame
pygame.init()
 
# 设置手柄
joystick = pygame.joystick.Joystick(0)
joystick.init()
 
print("使用的手柄名称:", joystick.get_name())
hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)
print(f"主机名: {hostname}")
print(f"本机 IP: {ip}")

UDP_IP = "192.168.88.231"  
UDP_PORT = 6006

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  

interval = 0.02  # 目标间隔 0.02 秒
next_time = time.time()
linear_speed = 0.0
linear_speedx = 0.0
linear_speedy = 0.0
angular_speed = 0.0
deadzone = 0.4
w_1 = 0.0
w_2 = 0.0
w_3 = 0.0
w_4 = 0.0
x_a = 0.4
x_b = 0.2
flag = 0
multiple_linear_speed = 0.5 ## maximun linear speed
multiple_angular_speed = 0.5 ## maximun angular_speed
 
try:
    while True:
            
        for event in pygame.event.get():
            if event.type == pygame.JOYBUTTONDOWN:
                print(f"按钮按下: {event.button}")
                if event.button ==10 :  # R2 减少角速度
                    multiple_angular_speed -= 0.1
                    multiple_angular_speed = max(0.2, multiple_angular_speed)  # 最小值为0.2
                    print("**************max angular speed   --")
                    print(multiple_angular_speed)
                if event.button == 9:  # R2 减少角速度
                    multiple_linear_speed -= 0.1
                    multiple_linear_speed = max(0.2, multiple_linear_speed)  # 最小值为0.2
                    print("**************max angular speed   --")
                    print(multiple_linear_speed)
                if event.button ==0 :  # R2 减少角速度
                    linear_speedx = 0
                    linear_speedy = 0
                    angular_speed = 0
            
            
            
            elif event.type == pygame.JOYAXISMOTION:
                print(f"摇杆移动: 轴{event.axis} 值{event.value}")
                
                # 1. 先处理倍率调整按钮（轴4/5）
                if event.axis == 4:
                    multiple_linear_speed += 0.1
                    multiple_linear_speed = max(0.2, multiple_linear_speed)
                    print("**************max linear speed ++")
                    print(multiple_linear_speed)
                
                elif event.axis == 5:
                    multiple_angular_speed += 0.1
                    multiple_angular_speed = max(0.2, multiple_angular_speed)
                    print("**************max angular speed ++")
                    print(multiple_angular_speed)
                
                # 2. 单独处理每个运动轴（互斥执行）
                elif event.axis == 3:  # 前后移动
                    if abs(event.value) < deadzone:  # 忽略微小移动
                        linear_speedy = 0
                    else:
                        linear_speedy = -event.value * multiple_linear_speed
                    print(linear_speedy)
                    flag = 1
                elif event.axis == 2:
                    if abs(event.value) < deadzone:  # 忽略微小移动
                        linear_speedx = 0
                    else:
                        linear_speedx = -event.value * multiple_linear_speed
                    print(linear_speedx)
                    flag = 1

                elif event.axis == 0:  # 旋转
                    if abs(event.value) < deadzone:  # 忽略微小移动
                        angular_speed = 0
                    else:
                        angular_speed = -event.value * multiple_angular_speed
                    print(angular_speed)
                    flag = 1

                # 3. 在所有轴处理完成后计算轮速（保持这个缩进级别）
                w_1 = (-linear_speedx + linear_speedy + (x_a + x_b) * angular_speed)*10
                w_1 = round(w_1)
                w_2 = (linear_speedx + linear_speedy - (x_a + x_b) * angular_speed)*10
                w_2 = round(w_2)
                w_3 = (-linear_speedx + linear_speedy - (x_a + x_b) * angular_speed)*10
                w_3 = round(w_3)
                w_4 = (linear_speedx + linear_speedy + (x_a + x_b) * angular_speed)*10
                w_4 = round(w_4)

            # 4. 打印计算结果
            print(w_1)
            print(w_2)
            print(w_3)
            print(w_4)
            print(type(w_4))
            if(flag):
                data = struct.pack('<4h',w_1,w_2,w_3,w_4)
                print("data:")
                print(data)
                sock.sendto(data,(UDP_IP,UDP_PORT))
            next_time += interval
            sleep_time = next_time - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)
            
            
            

except KeyboardInterrupt:
    print("停止读取手柄输入.")
finally:
    pygame.quit()