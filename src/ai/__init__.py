from WeiboBot import Weibo
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import (
    TencentCloudSDKException,
)
from tencentcloud.ims.v20201229 import ims_client, models
from loguru import logger
from config import setting
import base64
import json
import os
import asyncio
import tempfile
from typing import List


async def dectection(weibo: Weibo) -> bool:
    if weibo.video_url():
        if await video_classify(weibo.video_url()):
            return True
    if weibo.live_photo:
        for live_photo in weibo.live_photo:
            if await video_classify(video_url=live_photo):
                return True
    if weibo.image_list():
        for image in weibo.image_list():
            if await image_classify(image_url=image):
                return True
    return False


async def image_classify(image_url: str = "", base64_image: str = "") -> bool:
    """使用腾讯云图片内容安全服务对图片进行审核。

    该函数会对指定URL的图片进行内容安全审核，检查是否包含违规内容（如色情、暴力等）。
    为了提高性能，函数会维护一个已审核图片的缓存，避免重复审核相同的图片。

    Args:
        image_url (str): 需要审核的图片URL地址。
        base64_image (str): 图片的base64编码，如果提供则优先使用。

    Returns:
        bool: 是否违规
    """
    try:
        cred = credential.Credential(
            setting.tencent_api_key, setting.tencent_secret_key
        )
        client = ims_client.ImsClient(cred, "ap-guangzhou")
        req = models.ImageModerationRequest()
        if base64_image:
            params = {
                "FileContent": base64_image,
            }
        else:
            params = {
                "FileUrl": image_url,
            }
        req.from_json_string(json.dumps(params))
        resp = client.ImageModeration(req)
        for item in resp.LabelResults:
            if item.Label == "Porn" and item.Score >= 70:
                return True
            if item.Label == "Sexy" and item.Score >= 70:
                return True
        return False
    except TencentCloudSDKException as e:
        logger.error(f"腾讯云图片审查失败: {e}")
        return False


async def video_classify(video_url: str) -> bool:
    base64_frames = await extract_5_frames_base64(video_url)
    for frame in base64_frames:
        if await image_classify(base64_image=frame):
            return True
    return False


async def extract_5_frames_base64(video_url: str) -> List[str]:
    """从视频中提取5帧并转换为base64

    提取的视频帧包括：
    1. 视频开始
    2. 视频1/4处
    3. 视频1/2处
    4. 视频3/4处
    5. 视频结束前1秒

    Args:
        video_path: 本地视频文件路径

    Returns:
        List[str]: 5帧图片的base64编码列表
    """
    # 1. 获取视频总时长
    probe_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_url,  # 转换为字符串
    ]
    result = await asyncio.create_subprocess_exec(
        *probe_cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await result.communicate()
    if not stdout:
        return []
    duration = float(stdout.decode().strip())

    # 2. 时间戳列表，先均匀，再把最后一帧替换为 SSEOF
    timestamps = [duration * i / 4 for i in range(5)]

    base64_frames = []

    for idx, ts in enumerate(timestamps):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            img_path = tmp_file.name

        if idx == 4:
            # 最后一帧改用 sseof 定位，防止空帧
            ffmpeg_cmd = [
                "ffmpeg",
                "-sseof",
                "-1",  # 从结尾向前 1 秒
                "-i",
                video_url,  # 转换为字符串
                "-vframes",
                "1",
                "-q:v",
                "2",
                "-y",
                img_path,
            ]
        else:
            ffmpeg_cmd = [
                "ffmpeg",
                "-ss",
                str(ts),
                "-i",
                video_url,  # 转换为字符串
                "-vframes",
                "1",
                "-q:v",
                "2",
                "-y",
                img_path,
            ]

        proc = await asyncio.create_subprocess_exec(
            *ffmpeg_cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(
                f"ffmpeg failed at timestamp {ts if idx < 4 else 'last (sseof -1)'}"
            )

        with open(img_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
            base64_frames.append(b64)

        os.remove(img_path)

    return base64_frames
