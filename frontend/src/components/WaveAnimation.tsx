import { useEffect, useRef } from 'react';
import type { FC } from 'react';

export const WaveAnimation: FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let step = 0;

    const resize = () => {
      canvas.width = canvas.parentElement?.clientWidth || 700;
      canvas.height = 140;
    };
    resize();
    window.addEventListener('resize', resize);

    // Render multi-layered glowing ribbons matching Image 1
    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      step += 0.02;

      const width = canvas.width;
      const height = canvas.height;

      // Draw multiple nested sine ribbon curves
      const ribbonCount = 5;
      for (let r = 0; r < ribbonCount; r++) {
        ctx.beginPath();
        const offset = r * 0.18;
        const alpha = 0.25 + (r / ribbonCount) * 0.55;

        // Gradient for the ribbon: cyan -> violet -> pink/magenta
        const gradient = ctx.createLinearGradient(0, 0, width, height);
        gradient.addColorStop(0, `rgba(56, 189, 248, ${alpha * 0.3})`); // Cyan
        gradient.addColorStop(0.35, `rgba(168, 85, 247, ${alpha * 0.9})`); // Purple
        gradient.addColorStop(0.7, `rgba(217, 70, 239, ${alpha})`); // Violet/Magenta
        gradient.addColorStop(1, `rgba(244, 114, 182, ${alpha * 0.6})`); // Pink

        ctx.strokeStyle = gradient;
        ctx.lineWidth = r === ribbonCount - 1 ? 2.5 : 1.2;
        ctx.shadowBlur = r === ribbonCount - 1 ? 16 : 6;
        ctx.shadowColor = 'rgba(192, 132, 252, 0.7)';

        for (let x = 0; x <= width; x += 3) {
          const progress = x / width;
          // Dynamic dual-frequency sine wave with harmonic oscillation
          const y = height * 0.52 + 
            Math.sin(progress * Math.PI * 2.2 + step + offset) * (26 + r * 3) +
            Math.cos(progress * Math.PI * 4.0 - step * 0.6) * 10;
          
          if (x === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }
        ctx.stroke();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="absolute top-0 right-0 w-[58%] h-36 pointer-events-none overflow-hidden z-0">
      <canvas ref={canvasRef} className="w-full h-full opacity-90" />
    </div>
  );
};

