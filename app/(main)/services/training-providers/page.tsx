// Force server-side rendering, to get latest training provider logos
export const dynamic = "force-dynamic";

export default function Page() {
  return (
    <main>
      <div className="px-8 sm-tablet:px-12 tablet:px-24 laptop:px-64 flex-col justify-start items-center gap-5 inline-flex">
        <div className="self-stretch flex-col justify-center items-center gap-6 flex">
          <div className="mt-24 mb-12 self-stretch text-center text-cyan-700 text-6xl font-normal font-['Roboto'] capitalize leading-normal">
            Coalition Training Providers
          </div>
          <div className="self-stretch">
            <p className="text-zinc-900 text-xl font-normal font-['Roboto'] leading-loose">
              Employer members of The Coalition benefit from direct access to
              high quality talent pools offered by a dedicated network of
              training providers. Each training provider specializes in
              developing candidates from diverse backgrounds, preparing them
              with industry-recognized credentials and career-readiness training
              for in-demand Tech roles. Graduates range from veterans with Tech
              experience and security clearances to Seniors in BA/BAS degree
              programs who have undergone additional practical training to
              promising candidates from BIPOC and underrepresented communities.
            </p>
            <br />
            <p className="text-zinc-900 text-xl font-normal font-['Roboto'] leading-loose">
              Please browse the individual pages of our network training
              partners on this site to learn more.
            </p>
          </div>
        </div>
      </div>
      {/*<div className="mt-12 px-8 laptop:px-24">*/}
      {/*  <TrainingProviderMembers></TrainingProviderMembers>*/}
      {/*</div>*/}
    </main>
  );
}
