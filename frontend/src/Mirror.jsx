import React, { useRef, useEffect } from "react";
import * as bodyPix from "@tensorflow-models/body-pix";
import "@tensorflow/tfjs-backend-webgl";

export default function Mirror() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const webcamRef = useRef(null);

  useEffect(() => {
    const loadModelAndStart = async () => {
      const net = await bodyPix.load();

      const webcamStream = await navigator.mediaDevices.getUserMedia({ video: true });
      webcamRef.current.srcObject = webcamStream;

      const drawLoop = async () => {
        if (webcamRef.current.readyState === 4) {
          const segmentation = await net.segmentPerson(webcamRef.current, {
            internalResolution: "medium",
            segmentationThreshold: 0.7,
          });

          const ctx = canvasRef.current.getContext("2d");
          const imageData = ctx.createImageData(webcamRef.current.videoWidth, webcamRef.current.videoHeight);

          const mask = bodyPix.toMask(segmentation);

          // Draw webcam image first
          ctx.drawImage(videoRef.current, 0, 0, canvasRef.current.width, canvasRef.current.height);
          ctx.drawImage(webcamRef.current, 0, 0, canvasRef.current.width, canvasRef.current.height);

          // Then erase background using the mask
          const { data: imgData } = ctx.getImageData(0, 0, canvasRef.current.width, canvasRef.current.height);
          for (let i = 0; i < imgData.length; i += 4) {
            const maskVal = mask.data[i];
            if (maskVal === 0) {
              imgData[i + 3] = 0; // Set alpha to 0
            }
          }
          ctx.putImageData(new ImageData(imgData, canvasRef.current.width, canvasRef.current.height), 0, 0);
        }

        requestAnimationFrame(drawLoop);
      };

      drawLoop();
    };

    loadModelAndStart();
  }, []);

  return (
    <div className="relative w-full h-screen overflow-hidden">
      {/* Background looping video */}
      <video
        ref={videoRef}
        src="/video.mp4"
        autoPlay
        loop
        muted
        playsInline
        className="absolute top-0 left-0 w-full h-full object-cover z-0"
      />

      {/* Hidden webcam feed */}
      <video
        ref={webcamRef}
        autoPlay
        muted
        playsInline
        className="hidden"
      />

      {/* Canvas compositing foreground (person only) */}
      <canvas
        ref={canvasRef}
        className="absolute top-0 left-0 w-full h-full z-10"
      />
    </div>
  );
}
