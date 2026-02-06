import { UserCircleIcon } from "@heroicons/react/24/outline";
import Image from "next/image";

export default function Avatar({
  imgsrc,
  scale,
}: {
  imgsrc: string | undefined;
  scale?: number;
}) {
  let size = 85;
  if (scale) {
    size = Math.floor(85 * scale);
  }
  return (
    <div
      className={`flex justify-center items-center`}
      style={{ width: `${size}px`, height: `${size}px` }}
    >
      {imgsrc ? (
        <Image
          width={size}
          height={size}
          src={imgsrc}
          alt={""}
          className={`rounded-full object-cover aspect-square`}
        />
      ) : (
        <UserCircleIcon data-testid="default-avatar-icon" />
      )}
    </div>
  );
}
