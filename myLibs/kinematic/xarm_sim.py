import numpy as np
import math
import os

useNullSpace = 1
useDynamics = 1
ikMaxNumIterations=1000
ikSolver = 0
xarmEndEffectorIndex = 8
xarmNumDofs = 7 

ll = [-17]*xarmNumDofs
ul = [17]*xarmNumDofs
jr = [17]*xarmNumDofs
jointPositions=[0,0,0,0,0,0,0]
rp = jointPositions
jointPoses = jointPositions
class XArm7Sim(object):
  def __init__(self, bullet_client, offset):
    self.bullet_client = bullet_client
    self.offset = np.array(offset)
    self.jointPoses = [0]*xarmNumDofs
    #print("offset=",offset)
    flags = self.bullet_client.URDF_ENABLE_CACHED_GRAPHICS_SHAPES
    orn=[0,0,0,1]
    script_dir = os.path.dirname(__file__)
    urdf_path = os.path.join(script_dir, "meshes/xarm7_robot.urdf")
    self.xarm = self.bullet_client.loadURDF(urdf_path, np.array([0,0,0])+self.offset, orn, useFixedBase=True, flags=flags)
    index = 0
    for j in range(self.bullet_client.getNumJoints(self.xarm)):
      self.bullet_client.changeDynamics(self.xarm, j, linearDamping=0, angularDamping=0)
      info = self.bullet_client.getJointInfo(self.xarm, j)
  
      jointName = info[1]
      jointType = info[2]
      if (jointType == self.bullet_client.JOINT_PRISMATIC):
        
        self.bullet_client.resetJointState(self.xarm, j, jointPositions[index]) 
        index=index+1
      if (jointType == self.bullet_client.JOINT_REVOLUTE):
        self.bullet_client.resetJointState(self.xarm, j, jointPositions[index]) 
        index=index+1
  def reset(self):
    pass

  def calculate_joints(self, goal):
    pos = goal[:3]
    orn = self.bullet_client.getQuaternionFromEuler(goal[3:])
    #orn = [1,0,0,0]
    jointPoses = []
    if useNullSpace:
        restPoses = [0]*xarmNumDofs
        jointPoses = self.bullet_client.calculateInverseKinematics(self.xarm,xarmEndEffectorIndex, pos, orn,lowerLimits=ll, 
          upperLimits=ul,jointRanges=jr, restPoses=np.array(restPoses).tolist(),residualThreshold=1e-6, maxNumIterations=ikMaxNumIterations)
        
    else:
        self.jointPoses = self.bullet_client.calculateInverseKinematics(self.xarm,xarmEndEffectorIndex, pos, orn, maxNumIterations=ikMaxNumIterations)
    if useDynamics:
      for i in range(xarmNumDofs):
          pose = self.jointPoses[i]
          self.bullet_client.setJointMotorControl2(self.xarm, i+1, self.bullet_client.POSITION_CONTROL, pose,force=5 * 240.)
    else:
      for i in range(xarmNumDofs):
        self.bullet_client.resetJointState(self.xarm, i+1, jointPoses[i])

    return np.array(jointPoses)



    
  