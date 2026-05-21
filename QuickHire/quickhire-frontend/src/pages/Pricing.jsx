import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const plans = [
  {
    id: 'pay_per_use',
    name: 'Pay Per Use',
    price: '₹49',
    per: 'per screening',
    credits: '1 credit',
    color: 'border-gray-200',
    btn: 'bg-gray-800',
    features: ['1 screening credit', 'Up to 20 resumes', 'AI scoring', 'Excel export']
  },
  {
    id: 'monthly',
    name: 'Monthly',
    price: '₹1,999',
    per: 'per month',
    credits: '70 credits',
    color: 'border-blue-500',
    btn: 'bg-blue-900',
    popular: true,
    features: ['70 screening credits', 'Up to 20 resumes each', 'AI scoring + questions', 'Excel export', 'Priority support']
  },
  {
    id: 'annual',
    name: 'Annual',
    price: '₹19,999',
    per: 'per year',
    credits: '850 credits',
    color: 'border-purple-500',
    btn: 'bg-purple-700',
    features: ['Everything in Monthly', '850 screening credits', 'Save ₹3,998/year', 'Advanced analytics', 'Email automation', 'Dedicated support']
  }
];

export default function Pricing() {
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const [loading, setLoading] = useState('');

  const handleBuy = async (planId) => {
    if (!token) { navigate('/login'); return; }
    setLoading(planId);

    try {
      const res = await axios.post(
        `http://localhost:8000/payment/create-order?plan=${planId}&token=${token}`
      );
      const order = res.data;

      // Load Razorpay
      const options = {
        key: order.razorpay_key,
        amount: order.amount,
        currency: order.currency,
        name: 'QuickHire',
        description: order.description,
        order_id: order.order_id,
        prefill: {
          name: order.user_name,
          email: order.user_email,
          contact: order.user_phone
        },
        theme: { color: '#1B4F9E' },
        handler: async (response) => {
          try {
            await axios.post(
              `http://localhost:8000/payment/verify?razorpay_order_id=${response.razorpay_order_id}&razorpay_payment_id=${response.razorpay_payment_id}&razorpay_signature=${response.razorpay_signature}&token=${token}`
            );
            alert('✅ Payment successful! Credits added to your account.');
            navigate('/dashboard');
          } catch (err) {
            alert('Payment verification failed. Contact support.');
          }
        }
      };

      const rzp = new window.Razorpay(options);
      rzp.open();

    } catch (err) {
      alert('Failed to create order: ' + (err.response?.data?.detail || err.message));
    } finally {
      setLoading('');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-blue-900 text-white px-6 py-4 flex items-center gap-4">
        <button onClick={() => navigate('/dashboard')} className="hover:text-blue-200">← Back</button>
        <h1 className="text-xl font-bold">⚡ QuickHire Pricing</h1>
      </nav>

      {/* Load Razorpay script */}
      <script src="https://checkout.razorpay.com/v1/checkout.js"></script>

      <div className="max-w-5xl mx-auto p-8">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-800 mb-4">Simple, Transparent Pricing</h2>
          <p className="text-gray-500 text-lg">Start free, pay only when you need more</p>
        </div>

        {/* Free Plan */}
        <div className="bg-green-50 border border-green-200 rounded-2xl p-6 mb-8 text-center">
          <h3 className="text-xl font-bold text-green-700">🎁 Free Plan — Currently Active</h3>
          <p className="text-green-600 mt-2">You get 5 free screenings to get started. No credit card required!</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map(plan => (
            <div key={plan.id}
              className={`bg-white rounded-2xl p-8 shadow-sm border-2 ${plan.color} relative`}>
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-900 text-white text-xs px-4 py-1 rounded-full font-bold">
                  MOST POPULAR
                </div>
              )}
              <h3 className="text-xl font-bold text-gray-800 mb-2">{plan.name}</h3>
              <div className="mb-1">
                <span className="text-4xl font-bold text-gray-900">{plan.price}</span>
              </div>
              <p className="text-gray-400 text-sm mb-6">{plan.per}</p>

              <ul className="space-y-3 mb-8">
                {plan.features.map((f, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-gray-600">
                    <span className="text-green-500 font-bold">✓</span> {f}
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handleBuy(plan.id)}
                disabled={loading === plan.id}
                className={`w-full py-3 ${plan.btn} text-white rounded-xl font-bold hover:opacity-90 disabled:opacity-50 transition-all`}>
                {loading === plan.id ? '⏳ Processing...' : `Buy ${plan.name}`}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}