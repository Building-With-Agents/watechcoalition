"use client";

import React, { useEffect, useRef } from "react";

const HALF_PI = Math.PI * 0.5;

const timeStep = 1 / 120;

class Point {
  x: number;
  y: number;

  constructor(x = 0, y = 0) {
    this.x = x;
    this.y = y;
  }
}

class Particle {
  p0: Point;
  p1: Point;
  p2: Point;
  p3: Point;
  time: number;
  duration: number;
  color: string;
  w: number;
  h: number;
  complete: boolean;
  x: number;
  y: number;
  r: number;
  sy: number;

  constructor(p0: Point, p1: Point, p2: Point, p3: Point) {
    this.p0 = p0;
    this.p1 = p1;
    this.p2 = p2;
    this.p3 = p3;

    this.time = 0;
    this.duration = 3 + Math.random() * 2;
    this.color = "#" + Math.floor(Math.random() * 0xffffff).toString(16);

    this.w = 8;
    this.h = 6;

    this.complete = false;
    this.x = p0.x;
    this.y = p0.y;
    this.r = 0;
    this.sy = 1;
  }

  update() {
    this.time = Math.min(this.duration, this.time + timeStep);

    const f = Ease.outCubic(this.time, 0, 1, this.duration);
    const p = cubeBezier(this.p0, this.p1, this.p2, this.p3, f);

    const dx = p.x - this.x;
    const dy = p.y - this.y;

    this.r = Math.atan2(dy, dx) + HALF_PI;
    this.sy = Math.sin(Math.PI * f * 10);
    this.x = p.x;
    this.y = p.y;

    this.complete = this.time === this.duration;
  }

  draw(ctx: CanvasRenderingContext2D) {
    ctx.save();
    ctx.translate(this.x, this.y);
    ctx.rotate(this.r);
    ctx.scale(1, this.sy);

    ctx.fillStyle = this.color;
    ctx.fillRect(-this.w * 0.5, -this.h * 0.5, this.w, this.h);

    ctx.restore();
  }
}

const Ease = {
  inCubic(t: number, b: number, c: number, d: number) {
    t /= d;
    return c * t * t * t + b;
  },
  outCubic(t: number, b: number, c: number, d: number) {
    t /= d;
    t--;
    return c * (t * t * t + 1) + b;
  },
  inOutCubic(t: number, b: number, c: number, d: number) {
    t /= d / 2;
    if (t < 1) return (c / 2) * t * t * t + b;
    t -= 2;
    return (c / 2) * (t * t * t + 2) + b;
  },
  inBack(t: number, b: number, c: number, d: number, s = 1.70158) {
    return c * (t /= d) * t * ((s + 1) * t - s) + b;
  },
};

function cubeBezier(
  p0: Point,
  c0: Point,
  c1: Point,
  p1: Point,
  t: number,
): Point {
  const p = new Point();
  const nt = 1 - t;

  p.x =
    nt * nt * nt * p0.x +
    3 * nt * nt * t * c0.x +
    3 * nt * t * t * c1.x +
    t * t * t * p1.x;
  p.y =
    nt * nt * nt * p0.y +
    3 * nt * nt * t * c0.y +
    3 * nt * t * t * c1.y +
    t * t * t * p1.y;

  return p;
}

const Confetti: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const particles = useRef<Particle[]>([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d")!;
    initDrawingCanvas(ctx, canvas.clientWidth, canvas.clientHeight);

    const loop = () => {
      update();
      draw(ctx, canvas.clientWidth, canvas.clientHeight);

      if (checkParticlesComplete()) {
        // reset
        return;
      }

      requestAnimationFrame(loop);
    };

    loop();

    function initDrawingCanvas(
      ctx: CanvasRenderingContext2D,
      viewWidth: number,
      viewHeight: number,
    ) {
      const canvas = canvasRef.current!;
      canvas.width = viewWidth;
      canvas.height = viewHeight;

      createParticles(viewWidth, viewHeight);
    }
  }, []);

  const createParticles = (viewWidth: number, viewHeight: number) => {
    particles.current = [];
    for (let i = 0; i < 128; i++) {
      const p0 = new Point(viewWidth * 0.5, viewHeight * 0.5);
      const p1 = new Point(
        Math.random() * viewWidth,
        Math.random() * viewHeight,
      );
      const p2 = new Point(
        Math.random() * viewWidth,
        Math.random() * viewHeight,
      );
      const p3 = new Point(Math.random() * viewWidth, viewHeight + 64);

      particles.current.push(new Particle(p0, p1, p2, p3));
    }
  };

  const update = () => {
    particles.current.forEach((p) => p.update());
  };

  const draw = (
    ctx: CanvasRenderingContext2D,
    viewWidth: number,
    viewHeight: number,
  ) => {
    ctx.clearRect(0, 0, viewWidth, viewHeight);
    particles.current.forEach((p) => p.draw(ctx));
  };

  const checkParticlesComplete = () => {
    return particles.current.every((p) => p.complete);
  };

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed",
        height: "150vh",
        width: "100vw",
        top: "-50vh",
        left: 0,
        pointerEvents: "none",
      }}
    />
  );
};

export default Confetti;
