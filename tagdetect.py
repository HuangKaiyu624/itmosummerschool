import cv2
import numpy as np
import math
import socket
import struct
import time

# 全局设置
target_point = (200, 200)  # 目标点像素坐标 (x,y)
Kp_linear = 0.5  # 线性控制比例系数
Kp_angular = 0.8  # 角度控制比例系数
position_tolerance = 20  # 像素距离容差
global_v = 0.0
global_a = 0.0
global_angle = 0.0
global_distance = 0.0
global_linear_speedy = 0.0
global_angular_speed = 0.0
# 网络设置
hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)
print(f"主机名: {hostname}")
print(f"本机 IP: {ip}")

UDP_IP = "192.168.88.231"  
UDP_PORT = 6006
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  

# 麦克纳姆轮参数
x_a = 0.25  # 前后轮距/2
x_b = 0.25  # 左右轮距/2
linear_speedx = 0  # X方向线速度固定为0

def sendmessage(w1, w2, w3, w4):
    w1 = round(w1)
    w2 = round(w2)
    w3 = round(w3)
    w4 = round(w4)
    data = struct.pack('<4h', w1, w2, w3, w4)
    print("data:", data)
    sock.sendto(data, (UDP_IP, UDP_PORT))
    
def calculate_angle_between_lines(pt1, pt2, pt3, pt4):
    # """
    # 计算两条线的夹角：
    # 线1：pt1到pt2的连线
    # 线2：pt3到pt4的连线
    
    # 返回：
    #     两线夹角（角度制，0-180度）
    # """
    # 计算两条线的向量
    vec1 = np.array(pt2) - np.array(pt1)  # 第一条线向量
    vec2 = np.array(pt4) - np.array(pt3)  # 第二条线向量
    
    # 计算向量夹角（弧度）
    dot_product = np.dot(vec1, vec2)
    norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)
    
    # 处理可能的数值误差
    cos_theta = np.clip(dot_product / norm_product, -1.0, 1.0)
    angle_rad = np.arccos(cos_theta)
    
    # 转换为角度并确保在0-180度之间
    angle_deg = np.degrees(angle_rad) % 180
    
    return angle_deg

def detect_aruco_markers(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    detector = cv2.aruco.ArucoDetector(aruco_dict, cv2.aruco.DetectorParameters())
    corners, ids, _ = detector.detectMarkers(gray)
    
    if ids is not None:
        for i in range(len(ids)):
            if ids[i][0] == 31:  # 只检测ID=31的标记
                marker_corners = corners[i][0]
                center_x = int(np.mean(marker_corners[:, 0]))
                center_y = int(np.mean(marker_corners[:, 1]))
                
                # 绘制标记和中心点
                cv2.aruco.drawDetectedMarkers(frame, corners, ids)
                cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
                
                # 返回中心点和四个角点
                return (center_x, center_y), marker_corners, frame
    return None, None, frame

def calculate_wheel_speeds(linear_speedy, angular_speed):
    # 麦克纳姆轮转速计算
    w_1 = (-linear_speedx + linear_speedy + 0.5 * angular_speed) * 10
    w_2 = (linear_speedx + linear_speedy - 0.5 * angular_speed) * 10
    w_3 = (-linear_speedx + linear_speedy - 0.5 * angular_speed) * 10
    w_4 = (linear_speedx + linear_speedy + 0.5 * angular_speed) * 10

    return w_1, w_2, w_3, w_4

def calculate_control(current_pos, marker_corners):
    global global_v, global_a, global_angle, global_distance,global_angular_speed,global_linear_speedy
    
    # 计算中心点到目标点的距离
    dx = target_point[0] - current_pos[0]
    dy = target_point[1] - current_pos[1]
    distance = math.sqrt(dx**2 + dy**2)
    
    # 计算两条线的夹角
    # 线1：角点1到角点4的直线（标记的长边）
    # 线2：中心点到目标点的直线
    angle = calculate_angle_between_lines(
        marker_corners[0], marker_corners[3],  # 角点1和角点4
        current_pos, target_point              # 中心点和目标点
    )
    
    # 调整角度范围为-180到180度（用于转向控制）
    # 需要确定转向方向（顺时针/逆时针）
    cross_product = np.cross(
        np.array(marker_corners[3]) - np.array(marker_corners[0]),
        np.array(target_point) - np.array(current_pos)
    )
    
    # 如果叉积为负，角度取负
    if cross_product < 0:
        angle = -angle
    linear_speedy = 0
    # 简单比例控制
    if angle>2 :
        angular_speed = 30
    else:
        angular_speed = 0
        linear_speedy = 20  # 前进速度
    
    global_angle = angle
    global_distance = distance
    global_linear_speedy = linear_speedy
    global_angular_speed = angular_speed
    # 计算四轮转速
    w1, w2, w3, w4 = calculate_wheel_speeds(linear_speedy, angular_speed)
    
    return distance, w1, w2, w3, w4

def main():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    while True:
        ret, frame = cap.read()
        if not ret: break
        
        # 检测标记
        current_pos, marker_corners, frame = detect_aruco_markers(frame)
        
        if current_pos is not None and marker_corners is not None:
            # 计算控制量
            dist, w1, w2, w3, w4 = calculate_control(current_pos, marker_corners)
            w1 = int(w1)
            w2 = int(w2)
            w3 = int(w3)
            w4 = int(w4)
            # 可视化：绘制两条线
            # 线1：角点1到角点4
            cv2.line(frame, 
                     tuple(marker_corners[0].astype(int)), 
                     tuple(marker_corners[3].astype(int)), 
                     (255, 0, 0), 2)
            
            # 线2：中心点到目标点
            cv2.line(frame, 
                     tuple(np.array(current_pos).astype(int)), 
                     tuple(np.array(target_point).astype(int)), 
                     (0, 0, 255), 2)
            
            # 显示信息
            cv2.putText(frame, f"Pos: {current_pos}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"Target: {target_point}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"Angle: {global_angle:.1f}°", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"Wheels: {w1}, {w2}, {w3}, {w4}", (10, 120), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.putText(frame, f"speed: {global_angular_speed}, {global_linear_speedy}", (10, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # 检查是否到达目标
            if dist < position_tolerance:
                cv2.putText(frame, "ARRIVED!", (200, 200), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
                print("已到达目标点！")
                sendmessage(0, 0, 0, 0)
                time.sleep(1)  # 等待1秒
                break
            else:
                sendmessage(w1, w2, w3, w4)
        
        cv2.imshow("Mecanum Wheel Control", frame)
        if cv2.waitKey(1) == 27:  # ESC退出
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()