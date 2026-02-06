import Link from "next/link";
import RoundedButton from "./RoundedButton";

export default function RoundedButtonCard(props: {
  title: string;
  desc: string;
  callToAction: string;
  buttonText: string;
  link: string;
}) {
  return (
    <div className="border-box flex max-w-[400px] min-w-[375px] flex-col space-y-3 rounded-2xl border border-solid border-black px-5 py-5 shadow-xs">
      <h3 className="text-primary-600 font-bold text-lg">{props.title}</h3>
      <p>{props.desc}</p>
      <p>
        <Link className="text-primary-600" href={props.link}>
          {props.callToAction}
        </Link>
      </p>
      <div className="flex justify-end">
        <RoundedButton
          content={props.buttonText}
          link={props.link}
          invertColor={true}
        />
      </div>
    </div>
  );
}
