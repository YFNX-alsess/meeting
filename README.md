# 项目介绍

这是我（YFNX_alsess）用deepseek做的AIU二面项目。用LM studio部署了本地模型，用dify构建智能体，并接入本项目中。实现了基本的聊天功能和yolo的图片识别功能。


## 结构

```
.
├── README.md                                  #说明文档
├── TAsk_1.py                                  #阶段一任务
├── daily/                                     #工程日志
    ├── daily-10.5.md                     
    ├── daily-10.6.md                         
    └── photo/                            
        └── 屏幕截图 2026-10-05 171131.png
├── datasets/
    ├── coco8/                                 #第一次训练数据
    └── coco128/                               #第二次训练数据
├── index.html                                 #网页前端
├── main.py                                    #FASTAPI后端
├── predict_yoio.py                            #yolo推理文件
├── train_yoli.py                              #yolo训练文件
├── .env                                       #储存API和URL
├── requirements.txt                           #依赖库
└── yolov8n.pt                                 #官方模型

```

## 使用方法  

1. 安装Docker Desktop,LM studio,wsl等应用和环境；
2. 在wsl中安装dify；
3. 在LM studio中部署本地模型，加载，同时启动Docker Desktop；
4. 在wsl中启动dify（在dify部署目录中输入docker compose up -d）
5. 在浏览器中打开<http://localhost/install>,配置自身管理员账户和模型；
6. 在dify中创建一个应用（chatfollow），在访问点处获得API；
7. 在本项目根目录处创建.env文件；
```py
  DIFY_API_KEY=你的_dify_api_key
  DIFY_BASE_URL=http://localhost/v1
```
8. 安装python依赖；
```py
  pip install -r requirements.txt
```
9. 启动后端，在终端中输入：
```py
  uvicorn main:app --reload
```
10. 启动前端，双击index.html即可。

## 任务完成情况

1. 成功本地部署qwen3.5-4b,搭建智能体，接入web；
2. 成功跑通yolo，训练两次（第一次为coco8,十轮；第二次为coco128,30轮）；
3. 图像识别接入web。

## 其他

这个项目可以说是作者第一次做这种事情，作者的程序基础仅限于python的基本语法，如果没有人工智能的话，做这个项目跟要作者命没有如何区别。  
如前文所言，这个项目用了deepseek，所以会有很多不明所以的地方（因为作者自己都不知道有什么用）。  
关于大肥鱼（deep seek）的使用情况：  
1. 各种应用，环境，依赖的安装；
2. 代码的编写（手动复制粘贴）；
3. 改bug；
4. 创建该项目的初始文件夹；  

这个项目共用了0.25元的tokens。