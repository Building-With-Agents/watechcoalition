type ResendOptions = {
  from: string;
};

export const resendOptions: ResendOptions = {
  from: process.env.EMAIL_SENDER as string,
};
