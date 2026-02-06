import Image from "next/image";

export default function CircleBlurb() {
  return (
    <div className="scale-50 sm-tablet:scale-75 laptop:scale-100">
      <div className="w-[621.30px] h-[399.84px] relative ">
        <div className="w-[174px] h-[98.20px] left-0 top-[145.04px] absolute flex-col justify-start items-center gap-[21.22px] inline-flex">
          <div className="self-stretch h-[98.20px] flex-col justify-start items-center gap-[10.61px] flex">
            <div className="self-stretch h-[98.20px] flex-col justify-start items-center gap-[7.07px] flex">
              <div className="flex flex-wrap justify-center gap-1 w-[130px]">
                <div className="p-[3.54px] bg-black/10 rounded-[88.40px] justify-start items-center flex">
                  <div className="px-[5.30px] py-[2.65px] flex-col justify-start items-start inline-flex">
                    <div className="text-black/90 text-[13px] font-normal font-['Roboto'] leading-[18px] tracking-tight">
                      Svelte
                    </div>
                  </div>
                </div>
                <div className="p-[3.54px] bg-black/10 rounded-[88.40px] justify-start items-center flex">
                  <div className="px-[5.30px] py-[2.65px] flex-col justify-start items-start inline-flex">
                    <div className="text-black/90 text-[13px] font-normal font-['Roboto'] leading-[18px] tracking-tight">
                      Express
                    </div>
                  </div>
                </div>
                <div className="p-[3.54px] bg-black/10 rounded-[88.40px] justify-start items-center flex">
                  <div className="px-[5.30px] py-[2.65px] flex-col justify-start items-start inline-flex">
                    <div className="text-black/90 text-[13px] font-normal font-['Roboto'] leading-[18px] tracking-tight">
                      Node.js
                    </div>
                  </div>
                </div>
                <div className="p-[3.54px] bg-black/10 rounded-[88.40px] justify-start items-center flex">
                  <div className="px-[5.30px] py-[2.65px] flex-col justify-start items-start inline-flex">
                    <div className="text-black/90 text-[13px] font-normal font-['Roboto'] leading-[18px] tracking-tight">
                      Angular
                    </div>
                  </div>
                </div>
                <div className="p-[3.54px] bg-black/10 rounded-[88.40px] justify-start items-center flex">
                  <div className="px-[5.30px] py-[2.65px] flex-col justify-start items-start inline-flex">
                    <div className="text-black/90 text-[13px] font-normal font-['Roboto'] leading-[18px] tracking-tight">
                      React
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <Image
          className="left-[132.85px] top-0 absolute rounded-full"
          width={377}
          height={377}
          src="/images/stock/2DAvatar.png"
          alt={""}
        />
        <span className="w-[156.23px] h-[42.92px] left-[16.33px] top-[232.38px] absolute rounded-[7.07px] shadow-xs flex items-center justify-center bg-white border border-black">
          ADD PROJECTS
        </span>
        <span className="w-[174.25px] h-[42.92px] left-[447.05px] top-[301.44px] absolute rounded-[7.07px] shadow-xs flex items-center justify-center bg-white border border-black">
          ADD CERTIFICATES
        </span>

        <div className="w-[78.67px] h-[78.67px] left-[431.23px] top-[37px] absolute">
          <div className="w-[78.67px] h-[78.67px] left-0 top-0 absolute bg-[#047089] rounded-full" />
        </div>

        <span className="w-[221.62px] h-[42.92px] left-[320.42px] top-[356.92px] absolute rounded-[7.07px] shadow-xs flex items-center justify-center bg-white border border-black">
          ADD WORK EXPERIENCE
        </span>

        <div className="w-64 h-[87.61px] p-[18.81px] left-[39.28px] top-[297px] absolute bg-white rounded-[18.81px] shadow-xs flex-col justify-start items-start gap-[22.57px] inline-flex">
          <div className="flex-col justify-start items-start gap-[7.52px] flex">
            <div className="flex-col justify-start items-start flex">
              <div className="text-center text-black/90 text-[22.57px] font-bold font-['Roboto'] leading-[30.11px]">
                Jason Hayes
              </div>
              <div className="text-center text-black/90 text-[15.05px] font-normal font-['Roboto'] leading-tight">
                Software developer intern at CFA
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
