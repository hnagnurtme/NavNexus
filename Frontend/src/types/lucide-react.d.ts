declare module 'lucide-react' {
  import type { ForwardRefExoticComponent, RefAttributes, SVGProps } from 'react';

  type IconProps = Omit<SVGProps<SVGSVGElement>, 'ref'> & RefAttributes<SVGSVGElement>;

  export type LucideIcon = ForwardRefExoticComponent<IconProps>;

  export const ArrowRight: LucideIcon;
  export const BookOpen: LucideIcon;
  export const Briefcase: LucideIcon;
  export const LogIn: LucideIcon;
  export const LogOut: LucideIcon;
  export const Plus: LucideIcon;
  export const Search: LucideIcon;
  export const UserPlus: LucideIcon;
  export const Mail: LucideIcon;
  export const Lock: LucideIcon;
  export const User: LucideIcon;
  export const Loader2: LucideIcon;
  export const Github: LucideIcon;
  export const ArrowLeft: LucideIcon;
}


