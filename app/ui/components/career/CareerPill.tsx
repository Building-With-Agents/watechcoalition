import Link from "next/link";
import Image from "next/image";

export default function CareerPill({
  title,
  subtitle,
  img,
  href,
}: {
  title: string;
  subtitle?: string;
  img: string;
  href: string;
}) {
  return (
    <Link href={href}>
      <div className="w-full rounded-3xl shadow-xs flex-col justify-center items-center inline-flex bg-sky-100 hover:bg-sky-900 text-sky-900 hover:text-neutral-100">
        <Image
          src={img}
          height={4096}
          width={2731}
          alt="Stock photo"
          className="self-stretch grow shrink basis-0 rounded-tl-3xl rounded-tr-3xl"
        />
        <div className="p-6 rounded-bl-3xl rounded-br-3xl flex-col justify-start items-start gap-2.5 flex">
          <div className="flex-col justify-center items-start gap-2.5 flex">
            <div className="text-3xl font-normal font-['Roboto'] leading-10">
              {title}
            </div>
            <div className="self-stretch justify-start items-start gap-2.5 inline-flex">
              <div className="text-base font-semibold font-['Roboto'] uppercase leading-none tracking-wider">
                {subtitle}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
}
