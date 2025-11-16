// NaverToast.tsx
import { toast, Toaster } from 'react-hot-toast';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';

export const ToastNaver = {
  success: (msg: string) =>
    toast(msg, {
      icon: <CheckCircle2 size={20} />,
      style: {
        background: '#03C75A',
        color: '#fff',
        padding: '12px 20px',
        borderRadius: '10px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        fontWeight: 500,
      },
    }),
  error: (msg: string) =>
    toast(msg, {
      icon: <XCircle size={20} />,
      style: {
        background: '#FF3B30',
        color: '#fff',
        padding: '12px 20px',
        borderRadius: '10px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        fontWeight: 500,
      },
    }),
  loading: (msg: string) =>
    toast.loading(msg, {
      icon: <Loader2 className="animate-spin" size={20} />,
      style: {
        background: '#03C75A',
        color: '#fff',
        padding: '12px 20px',
        borderRadius: '10px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        fontWeight: 500,
      },
    }),
};


export const NaverToaster = () => <Toaster position="top-center" />;
